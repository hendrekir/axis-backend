"""
Dispatch service v2 — the Axis heartbeat, now skills-aware.

Runs every 15 minutes via APScheduler.
For each connected user:
1. Fetch new data from all connected sources
2. Assemble context (mode, tasks, thread history, user_model, skills)
3. Call Claude with the v2 dispatch prompt (skills + multi-model aware)
4. Parse structured JSON response
5. Route each item to the correct surface + skill
6. Run dispatch-triggered skills
7. Update last_dispatch_run timestamp
"""

import json
import logging
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Task, ThreadMessage, UserModel, Interaction, Skill
from prompts.dispatch_v2 import DISPATCH_V2_SYSTEM
from services.claude_service import generate
from services.gmail_service import fetch_recent_emails
from services.push_service import send_push
from services.skill_engine import run_dispatch_skills

logger = logging.getLogger("axis.dispatch")


async def _build_context(user: User, db: AsyncSession) -> dict:
    """Assemble the full context window for a single user."""

    # Active tasks (top 10 by position)
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user.id, Task.is_done == False)
        .order_by(Task.position)
        .limit(10)
    )
    tasks = result.scalars().all()
    tasks_text = "\n".join(
        f"- {t.title} ({t.category}, {'URGENT' if t.is_urgent else 'normal'})"
        for t in tasks
    ) or "No active tasks."

    # Recent thread messages (last 10)
    result = await db.execute(
        select(ThreadMessage)
        .where(ThreadMessage.user_id == user.id)
        .order_by(ThreadMessage.created_at.desc())
        .limit(10)
    )
    recent = result.scalars().all()
    thread_text = "\n".join(
        f"{m.role}: {m.content[:200]}" for m in reversed(recent)
    ) or "No recent thread history."

    # User model (learned patterns)
    result = await db.execute(
        select(UserModel).where(UserModel.user_id == user.id)
    )
    user_model = result.scalar_one_or_none()
    model_summary = "No user model yet."
    if user_model:
        parts = []
        if user_model.voice_patterns:
            parts.append(f"Voice: {json.dumps(user_model.voice_patterns)[:200]}")
        if user_model.productive_windows:
            parts.append(f"Productive windows: {json.dumps(user_model.productive_windows)[:200]}")
        if user_model.defer_patterns:
            parts.append(f"Defer patterns: {json.dumps(user_model.defer_patterns)[:200]}")
        model_summary = "\n".join(parts) if parts else "User model exists but empty."

    # Active skills
    result = await db.execute(
        select(Skill).where(Skill.user_id == user.id, Skill.is_active == True)
    )
    skills = result.scalars().all()
    skills_text = ", ".join(
        f"{s.name} ({s.reasoning_model}, trigger={s.trigger_type})" for s in skills
    ) or "No active skills."

    # Calendar events (if connected)
    calendar_text = ""
    if user.calendar_connected:
        try:
            from services.calendar_service import fetch_upcoming_events
            events = await fetch_upcoming_events(user, db, hours_ahead=12, max_results=5)
            if events:
                calendar_text = "\n\nUpcoming calendar events:\n" + "\n".join(
                    f"- {e['summary']} at {e['start_dt']} ({e['location'] or 'no location'})"
                    for e in events
                )
        except Exception as e:
            logger.warning("Calendar fetch failed for user %s: %s", user.id, e)

    return {
        "tasks": tasks_text,
        "recent_context": thread_text,
        "user_model_summary": model_summary,
        "active_skills": skills_text,
        "calendar_context": calendar_text,
    }


async def _route_item(item: dict, user: User, db: AsyncSession):
    """Route a single dispatch item to the correct surface."""
    surface = item.get("surface", "silent")
    action_type = item.get("action_type", "none")
    urgency = item.get("urgency", 1)
    reason = item.get("reason", "")
    prepared = item.get("pre_prepared_action", "")
    source = item.get("source", "unknown")

    # --- Silent: log only, don't surface ---
    if surface == "silent":
        logger.debug("Silent: %s — %s", item.get("summary", ""), reason)
        db.add(Interaction(
            user_id=user.id,
            surface="silent",
            content_type=source,
            content_id=item.get("item_id"),
            action_taken="filtered",
            mode=user.mode,
        ))
        return

    # --- Thread message for push / thread / widget / digest ---
    summary = item.get("summary", item.get("subject", "New item"))
    content = f"**{summary}**\n{reason}"
    if prepared and action_type == "send_reply":
        content += f"\n\nDraft reply ready:\n{prepared}"
    elif prepared and action_type == "create_task":
        content += f"\n\nSuggested task: {prepared}"
    elif prepared:
        content += f"\n\n{prepared}"

    msg = ThreadMessage(
        user_id=user.id,
        role="assistant",
        content=content,
        message_type="intel",
        source_skill=item.get("skill_name", "dispatch"),
    )
    db.add(msg)

    # --- Push notification ---
    if surface == "push" and user.apns_token:
        title = f"[{urgency}/10] {summary[:60]}"
        body = reason[:100]
        await send_push(user.apns_token, title, body, data={
            "action_type": action_type,
            "item_id": item.get("item_id", ""),
            "skill": item.get("skill_name", ""),
        })

    # --- Log interaction ---
    db.add(Interaction(
        user_id=user.id,
        surface=surface,
        content_type=source,
        content_id=item.get("item_id"),
        action_taken="surfaced",
        mode=user.mode,
    ))


async def dispatch_user(user: User, db: AsyncSession) -> dict:
    """Run the full dispatch cycle for one user."""
    stats = {
        "user_id": str(user.id),
        "emails_fetched": 0,
        "pushed": 0,
        "threaded": 0,
        "silent": 0,
        "digest": 0,
        "skills_run": 0,
    }

    # 1. Fetch new data from connected sources
    new_data_parts = []

    # Gmail
    if user.gmail_connected:
        emails = await fetch_recent_emails(
            user, db, after=user.last_dispatch_run, max_results=20
        )
        unread = [e for e in emails if e.get("is_unread")]
        stats["emails_fetched"] = len(unread)
        if unread:
            emails_text = "\n\n".join(
                f"[gmail] ID: {e['id']} | From: {e['from']} | Subject: {e['subject']} | Preview: {e['snippet']}"
                for e in unread
            )
            new_data_parts.append(emails_text)

    # Calendar
    if user.calendar_connected:
        try:
            from services.calendar_service import fetch_upcoming_events
            events = await fetch_upcoming_events(user, db, hours_ahead=4, max_results=5)
            if events:
                cal_text = "\n".join(
                    f"[calendar] {e['summary']} at {e['start_dt']} — {len(e.get('attendees', []))} attendees"
                    for e in events
                )
                new_data_parts.append(cal_text)
        except Exception as e:
            logger.warning("Calendar fetch failed in dispatch for user %s: %s", user.id, e)

    new_data = "\n\n".join(new_data_parts) if new_data_parts else "No new data inputs."

    # Skip Claude call if no new data
    if not new_data_parts:
        logger.info("No new data for user %s — running dispatch skills only", user.id)
        # Still run dispatch-triggered skills
        skill_results = await run_dispatch_skills(user, db)
        stats["skills_run"] = len(skill_results)
        user.last_dispatch_run = datetime.utcnow()
        await db.commit()
        return stats

    # 2. Assemble context
    ctx = await _build_context(user, db)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    prompt = DISPATCH_V2_SYSTEM.format(
        name=user.name or "there",
        mode=user.mode,
        timezone=user.timezone,
        current_time=now,
        active_skills=ctx["active_skills"],
        user_model_summary=ctx["user_model_summary"],
        tasks=ctx["tasks"],
        recent_context=ctx["recent_context"],
        new_data=new_data + ctx.get("calendar_context", ""),
    )

    # 3. Call Claude for classification
    raw = await generate(
        system_prompt="You are Axis. Return only valid JSON.",
        user_message=prompt,
        max_tokens=2048,
    )

    # 4. Parse response (strip markdown fences)
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    try:
        data = json.loads(cleaned)
        items = data.get("items", [])
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON for user %s: %s", user.id, raw[:300])
        user.last_dispatch_run = datetime.utcnow()
        await db.commit()
        return stats

    # 5. Route each item
    for item in items:
        surface = item.get("surface", "silent")
        stats[{"push": "pushed", "thread": "threaded", "digest": "digest"}.get(surface, "silent")] += 1
        await _route_item(item, user, db)

    # 6. Run dispatch-triggered skills
    skill_results = await run_dispatch_skills(user, db)
    stats["skills_run"] = len(skill_results)

    # 7. Update last_dispatch_run
    user.last_dispatch_run = datetime.utcnow()
    await db.commit()

    logger.info(
        "Dispatch v2 complete for %s: %d emails, %d pushed, %d threaded, %d silent, %d skills",
        user.name, stats["emails_fetched"], stats["pushed"], stats["threaded"],
        stats["silent"], stats["skills_run"],
    )
    return stats


async def run_dispatch(db: AsyncSession) -> list[dict]:
    """Run dispatch for ALL connected users. Called by cron or manual trigger."""
    result = await db.execute(
        select(User).where(
            (User.gmail_connected == True) | (User.calendar_connected == True)
        )
    )
    users = result.scalars().all()

    if not users:
        logger.info("No connected users found")
        return []

    all_stats = []
    for user in users:
        logger.info("Dispatching for %s (%s)", user.name, user.id)
        stats = await dispatch_user(user, db)
        all_stats.append(stats)

    return all_stats
