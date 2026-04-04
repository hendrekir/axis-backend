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

from models import User, Task, ThreadMessage, UserModel, Interaction, Skill, AgentActivity
from prompts.dispatch_v2 import DISPATCH_V2_SYSTEM
from services.claude_service import generate
from services.gmail_service import fetch_recent_emails
from services.push_service import send_push
from services.skill_engine import run_dispatch_skills
from services.triage_service import triage_items
from services.signal_filter import apply_filters
from services.followup_service import scan_for_missing_replies

logger = logging.getLogger("axis.dispatch")

# Patterns that indicate internal/debug content that should never reach the thread
_INTERNAL_PATTERNS = re.compile(
    r"(triage[_ ]?score|urgency[_ ]?score|surface[_ ]?routing|model_to_use|action_type"
    r"|appropriate for|morning digest|noise[_ ]?filtered)",
    re.IGNORECASE,
)


def _sanitize_content(text: str) -> str:
    """Strip lines containing internal classification language."""
    lines = text.split("\n")
    clean = [ln for ln in lines if not _INTERNAL_PATTERNS.search(ln)]
    return "\n".join(clean).strip()


def format_signal_for_thread(item: dict) -> str:
    """Build human-facing thread content from a dispatch item."""
    title = (
        item.get("title")
        or item.get("action")
        or item.get("summary")
        or "New signal"
    )
    action = item.get("pre_prepared_action", "")
    if action and action.strip():
        raw = f"{title}\n\n{action}"
    else:
        raw = title
    return _sanitize_content(raw)


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
    source = item.get("source", "unknown")

    # --- Silent: log only, don't surface ---
    if surface == "silent":
        logger.debug("Silent: %s — %s", item.get("summary", ""), item.get("reason", ""))
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
    content = format_signal_for_thread(item)

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
        push_title = (item.get("title") or item.get("action") or item.get("summary") or "New signal")[:60]
        body = (item.get("pre_prepared_action") or "")[:100]
        await send_push(user.apns_token, push_title, body, data={
            "action_type": item.get("action_type", "none"),
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


async def _generate_email_draft(item: dict, user: User, db: AsyncSession) -> str:
    """Generate a voice-matched email draft for urgent reply items."""
    from prompts.email_draft import EMAIL_DRAFT_SYSTEM

    # Load voice patterns from user model
    result = await db.execute(
        select(UserModel).where(UserModel.user_id == user.id)
    )
    user_model = result.scalar_one_or_none()
    voice_patterns = json.dumps(user_model.voice_patterns or {}) if user_model else "{}"

    prompt = EMAIL_DRAFT_SYSTEM.format(
        name=user.name or "there",
        voice_patterns=voice_patterns,
        sender=item.get("from", item.get("sender", "unknown")),
        subject=item.get("subject", item.get("summary", "")),
        email_body=item.get("snippet", item.get("preview", "")),
        thread_context=item.get("reason", ""),
    )

    draft = await generate(
        system_prompt="You are drafting an email reply. Return ONLY the email body text, nothing else.",
        user_message=prompt,
        max_tokens=512,
    )
    return draft.strip()


async def dispatch_user(user: User, db: AsyncSession) -> dict:
    """Run the full dispatch cycle for one user."""
    stats = {
        "user_id": str(user.id),
        "emails_fetched": 0,
        "items_triaged": 0,
        "noise_filtered": 0,
        "pushed": 0,
        "threaded": 0,
        "silent": 0,
        "digest": 0,
        "drafts_generated": 0,
        "skills_run": 0,
    }

    # 1. Fetch new data from connected sources
    raw_items = []  # Unified list for triage

    # Gmail
    if user.gmail_connected:
        emails = await fetch_recent_emails(
            user, db, after=user.last_dispatch_run, max_results=20
        )
        unread = [e for e in emails if e.get("is_unread")]
        stats["emails_fetched"] = len(unread)
        for e in unread:
            raw_items.append({
                "id": e.get("id", ""),
                "source": "gmail",
                "summary": f"{e.get('from', 'Unknown')}: {e.get('subject', '')}",
                "subject": e.get("subject", ""),
                "from": e.get("from", ""),
                "snippet": e.get("snippet", ""),
                "is_unread": True,
            })

    # Calendar
    if user.calendar_connected:
        try:
            from services.calendar_service import fetch_upcoming_events
            events = await fetch_upcoming_events(user, db, hours_ahead=4, max_results=5)
            for e in events:
                raw_items.append({
                    "id": e.get("id", ""),
                    "source": "calendar",
                    "summary": f"{e['summary']} at {e['start_dt']}",
                    "attendees": e.get("attendees", []),
                    "location": e.get("location", ""),
                })
        except Exception as e:
            logger.warning("Calendar fetch failed in dispatch for user %s: %s", user.id, e)

    # Skip if no new data
    if not raw_items:
        logger.info("No new data for user %s — running dispatch skills only", user.id)
        skill_results = await run_dispatch_skills(user, db)
        stats["skills_run"] = len(skill_results)
        user.last_dispatch_run = datetime.utcnow()
        await db.commit()
        return stats

    # 2. TRIAGE — cheap Gemini pre-filter, discard noise before Claude
    ctx = await _build_context(user, db)
    user_profile = {
        "name": user.name or "User",
        "mode": user.mode,
        "tasks": ctx["tasks"],
        "calendar": ctx.get("calendar_context", "None"),
    }

    triage_result = await triage_items(raw_items, user_profile)
    stats["items_triaged"] = len(raw_items)
    noise_count = len(triage_result["noise"])
    stats["noise_filtered"] = noise_count

    # Log noise count to agent_activity
    if noise_count > 0:
        db.add(AgentActivity(
            user_id=user.id,
            skill="dispatch",
            action="triage_noise_filtered",
            detail=f"{noise_count} items filtered as noise out of {len(raw_items)} total",
        ))

    # Only urgent + relevant proceed to Claude
    items_for_claude = triage_result["urgent"] + triage_result["relevant"]

    if not items_for_claude:
        logger.info("All %d items triaged as noise for user %s", len(raw_items), user.id)
        skill_results = await run_dispatch_skills(user, db)
        stats["skills_run"] = len(skill_results)
        user.last_dispatch_run = datetime.utcnow()
        await db.commit()
        return stats

    # 3. Assemble context and call Claude with only the surviving items
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    new_data = "\n\n".join(
        f"[{item['source']}] ID: {item['id']} | {item['summary']} | triage_score: {item.get('score', '?')}"
        for item in items_for_claude
    )

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

    raw = await generate(
        system_prompt="You are Axis. Return only valid JSON.",
        user_message=prompt,
        max_tokens=2048,
    )

    # 4. Parse response
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

    # 5. SIGNAL FILTER — 5-layer noise reduction on Claude's output
    filtered = await apply_filters(items, user.id, user.mode, db)

    # 6. Auto-generate email drafts for urgency 8+ reply items
    for item in filtered["push"]:
        urgency = item.get("urgency", item.get("score", 0))
        action_type = item.get("action_type", "")
        if urgency >= 8 and action_type == "send_reply" and item.get("source") == "gmail":
            try:
                # Find the original email data for this item
                original = next(
                    (r for r in raw_items if r.get("id") == item.get("item_id", item.get("id"))),
                    item,
                )
                merged = {**original, **item}
                draft = await _generate_email_draft(merged, user, db)
                item["pre_prepared_action"] = draft
                stats["drafts_generated"] += 1
                logger.info("Auto-drafted reply for user %s: %s", user.name, item.get("summary", "")[:60])
            except Exception as e:
                logger.warning("Email draft generation failed for user %s: %s", user.id, e)

    # 7. Route filtered items
    for item in filtered["push"]:
        item["surface"] = "push"
        stats["pushed"] += 1
        await _route_item(item, user, db)

    for item in filtered["digest"]:
        item["surface"] = "digest"
        stats["digest"] += 1
        await _route_item(item, user, db)

    for item in filtered["silent"]:
        item["surface"] = "silent"
        stats["silent"] += 1
        await _route_item(item, user, db)

    # 8. Run dispatch-triggered skills
    skill_results = await run_dispatch_skills(user, db)
    stats["skills_run"] = len(skill_results)

    # 8b. Follow-up tracker — surface unreplied emails
    if user.gmail_connected:
        try:
            followups = await scan_for_missing_replies(user, db)
            for fu in followups:
                fu["surface"] = "digest"
                stats["digest"] += 1
                await _route_item(fu, user, db)
        except Exception as e:
            logger.warning("Follow-up scan failed for user %s: %s", user.id, e)

    # 9. Update last_dispatch_run
    user.last_dispatch_run = datetime.utcnow()
    await db.commit()

    logger.info(
        "Dispatch v3 complete for %s: %d fetched, %d triaged, %d noise, %d pushed, %d digest, %d silent, %d drafts, %d skills",
        user.name, stats["emails_fetched"], stats["items_triaged"], stats["noise_filtered"],
        stats["pushed"], stats["digest"], stats["silent"], stats["drafts_generated"], stats["skills_run"],
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

    all_stats = []
    for user in users:
        logger.info("Dispatching for %s (%s)", user.name, user.id)
        stats = await dispatch_user(user, db)
        all_stats.append(stats)

    # Piggyback time-based notifications onto the 15-min dispatch cycle.
    # Each function checks per-user local time internally.
    try:
        from services.notification_service import send_journal_prompts, send_streak_reminders
        await send_journal_prompts(db)
        await send_streak_reminders(db)
    except Exception as e:
        logger.warning("Notification cycle failed: %s", e)

    return all_stats
