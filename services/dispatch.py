"""
Dispatch service — the Axis heartbeat.

Runs every 15 minutes via Railway cron or manual trigger.
For each Gmail-connected user:
1. Fetch new emails since last_dispatch_run
2. Assemble context (mode, tasks, thread history, user_model)
3. Call Claude with the dispatch prompt
4. Parse structured JSON response
5. Route each item to the correct surface (push|thread|widget|digest|silent)
6. Update last_dispatch_run timestamp
"""

import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Task, ThreadMessage, UserModel, Interaction
from prompts.dispatch import DISPATCH_SYSTEM
from services.claude_service import generate
from services.gmail_service import fetch_recent_emails
from services.push_service import send_push

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

    # User model (learned patterns) — may not exist yet
    result = await db.execute(
        select(UserModel).where(UserModel.user_id == user.id)
    )
    user_model = result.scalar_one_or_none()
    model_text = ""
    if user_model:
        model_text = (
            f"Voice patterns: {json.dumps(user_model.voice_patterns)}\n"
            f"Productive windows: {json.dumps(user_model.productive_windows)}\n"
            f"Completion rates: {json.dumps(user_model.completion_rates)}\n"
            f"Defer patterns: {json.dumps(user_model.defer_patterns)}"
        )

    return {
        "tasks": tasks_text,
        "recent_context": thread_text,
        "user_model": model_text,
    }


async def _route_item(item: dict, user: User, db: AsyncSession):
    """Route a single dispatch item to the correct surface."""
    surface = item.get("surface", "silent")
    action_type = item.get("action_type", "none")
    urgency = item.get("urgency", 1)
    reason = item.get("reason", "")
    prepared = item.get("pre_prepared_action", "")

    # --- Silent: log only, don't surface ---
    if surface == "silent":
        logger.debug("Silent: %s — %s", item.get("subject", ""), reason)
        db.add(Interaction(
            user_id=user.id,
            surface="silent",
            content_type="email",
            content_id=item.get("email_id"),
            action_taken="filtered",
            mode=user.mode,
        ))
        return

    # --- Thread message for push / thread / widget / digest ---
    content = f"**{item.get('subject', 'Email')}** from {item.get('from', 'unknown')}\n{reason}"
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
        source_skill="dispatch",
    )
    db.add(msg)

    # --- Push notification for push surface ---
    if surface == "push" and user.apns_token:
        title = f"[{urgency}/10] {item.get('subject', 'New signal')}"
        body = reason[:100]
        await send_push(user.apns_token, title, body, data={
            "action_type": action_type,
            "email_id": item.get("email_id", ""),
        })

    # --- Log interaction for feedback loop ---
    db.add(Interaction(
        user_id=user.id,
        surface=surface,
        content_type="email",
        content_id=item.get("email_id"),
        action_taken="surfaced",
        mode=user.mode,
    ))


async def dispatch_user(user: User, db: AsyncSession) -> dict:
    """Run the full dispatch cycle for one user. Returns stats."""
    stats = {"user_id": str(user.id), "emails_fetched": 0, "pushed": 0, "threaded": 0, "silent": 0, "digest": 0}

    # 1. Fetch emails since last dispatch (or last 20 if first run)
    emails = await fetch_recent_emails(
        user, db, after=user.last_dispatch_run, max_results=20
    )
    if not emails:
        logger.info("No new emails for user %s", user.id)
        user.last_dispatch_run = datetime.utcnow()
        await db.commit()
        return stats

    stats["emails_fetched"] = len(emails)

    # Filter to unread only
    unread = [e for e in emails if e.get("is_unread")]
    if not unread:
        logger.info("No unread emails for user %s", user.id)
        user.last_dispatch_run = datetime.utcnow()
        await db.commit()
        return stats

    # 2. Assemble context
    ctx = await _build_context(user, db)
    emails_text = "\n\n".join(
        f"Email ID: {e['id']}\nFrom: {e['from']}\nSubject: {e['subject']}\n"
        f"Date: {e['date']}\nPreview: {e['snippet']}"
        for e in unread
    )

    now = datetime.now().strftime("%Y-%m-%d %H:%M %Z")
    prompt = DISPATCH_SYSTEM.format(
        name=user.name or "there",
        mode=user.mode,
        timezone=user.timezone,
        current_time=now,
        tasks=ctx["tasks"],
        recent_context=ctx["recent_context"],
        emails=emails_text,
    )

    # 3. Call Claude
    raw = await generate(
        system_prompt="You are Axis. Return only valid JSON.",
        user_message=prompt,
        max_tokens=2048,
    )

    # 4. Parse response
    try:
        data = json.loads(raw)
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

    # 6. Update last_dispatch_run
    user.last_dispatch_run = datetime.utcnow()
    await db.commit()

    logger.info(
        "Dispatch complete for %s: %d emails, %d pushed, %d threaded, %d silent",
        user.name, stats["emails_fetched"], stats["pushed"], stats["threaded"], stats["silent"],
    )
    return stats


async def run_dispatch(db: AsyncSession) -> list[dict]:
    """Run dispatch for ALL Gmail-connected users. Called by cron or manual trigger."""
    result = await db.execute(
        select(User).where(User.gmail_connected == True)
    )
    users = result.scalars().all()

    if not users:
        logger.info("No Gmail-connected users found")
        return []

    all_stats = []
    for user in users:
        logger.info("Dispatching for %s (%s)", user.name, user.id)
        stats = await dispatch_user(user, db)
        all_stats.append(stats)

    return all_stats
