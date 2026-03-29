"""
Morning digest — generates a daily brief at 6:50AM user local time.

Pulls overnight emails, active tasks, thread history, and user_model.
Calls Claude to produce 3-4 short thread messages. Sends a push notification.
"""

import json
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from models import User, Task, ThreadMessage, UserModel, Interaction
from services.claude_service import generate
from services.gmail_service import fetch_recent_emails
from services.push_service import send_push

logger = logging.getLogger("axis.digest")

DIGEST_SYSTEM = """
You are Axis. Generate {name}'s morning brief as thread messages.
Specific, warm, direct. Never waffle.
Max 4 messages. Each under 80 words.
End the final message with "Your move: [specific next action]." — always give the user a clear next step. Never suggest disengaging or putting the phone down.

Current mode: {mode}
Today: {date}
Timezone: {timezone}

Overnight emails ({email_count} new):
{email_summary}

Active tasks:
{tasks}

Recent thread context:
{recent_context}

Axis handled silently overnight: {silent_count} items

Return ONLY a JSON array of message strings, no markdown fences:
["message 1", "message 2", "message 3"]
"""


async def generate_digest(user: User, db: AsyncSession) -> str:
    """Generate a morning digest for a single user. Returns the digest text."""

    # Active tasks
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

    # Recent thread messages
    result = await db.execute(
        select(ThreadMessage)
        .where(ThreadMessage.user_id == user.id)
        .order_by(ThreadMessage.created_at.desc())
        .limit(5)
    )
    recent = result.scalars().all()
    context_text = "\n".join(
        f"{m.role}: {m.content[:200]}" for m in reversed(recent)
    ) or "No recent thread history."

    # Overnight emails (last 12 hours)
    email_summary = "Gmail not connected."
    email_count = 0
    if user.gmail_connected:
        since = datetime.utcnow() - timedelta(hours=12)
        emails = await fetch_recent_emails(user, db, after=since, max_results=30)
        email_count = len(emails)
        if emails:
            email_summary = "\n".join(
                f"- {e['from']}: {e['subject']} — {e['snippet'][:80]}"
                for e in emails[:15]  # Cap at 15 for prompt size
            )
        else:
            email_summary = "No new emails overnight."

    # Count silent interactions from overnight dispatch
    result = await db.execute(
        select(Interaction)
        .where(
            Interaction.user_id == user.id,
            Interaction.surface == "silent",
            Interaction.created_at >= datetime.utcnow() - timedelta(hours=12),
        )
    )
    silent_count = len(result.scalars().all())

    # Build prompt
    try:
        user_tz = ZoneInfo(user.timezone)
    except Exception:
        user_tz = ZoneInfo("Australia/Brisbane")

    now_local = datetime.now(user_tz)
    prompt = DIGEST_SYSTEM.format(
        name=user.name or "there",
        mode=user.mode,
        date=now_local.strftime("%A, %B %d %Y"),
        timezone=user.timezone,
        email_summary=email_summary,
        email_count=email_count,
        tasks=tasks_text,
        recent_context=context_text,
        silent_count=silent_count,
    )

    # Call Claude
    raw = await generate(
        system_prompt="You are Axis. Return only a JSON array of message strings.",
        user_message=prompt,
        max_tokens=1024,
    )

    # Strip markdown fences if present (```json ... ```)
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    # Parse messages and save to thread
    try:
        messages = json.loads(cleaned)
        if not isinstance(messages, list):
            messages = [cleaned]
    except json.JSONDecodeError:
        messages = [cleaned]

    full_digest = ""
    for text in messages:
        msg = ThreadMessage(
            user_id=user.id,
            role="assistant",
            content=text,
            message_type="intel",
            source_skill="digest",
        )
        db.add(msg)
        full_digest += text + "\n\n"

    await db.commit()

    # Push notification
    if user.apns_token:
        preview = messages[0][:100] if messages else "Your morning brief is ready."
        await send_push(user.apns_token, "Morning Brief", preview)

    return full_digest.strip()


def _is_digest_time(user: User) -> bool:
    """Check if it's approximately 6:50AM in the user's timezone."""
    try:
        user_tz = ZoneInfo(user.timezone)
    except Exception:
        user_tz = ZoneInfo("Australia/Brisbane")

    now_local = datetime.now(user_tz)
    # Target 6:50 AM — allow a 15-minute window (6:45–7:00)
    return now_local.hour == 6 and 45 <= now_local.minute <= 59


async def run_morning_digest(db: AsyncSession) -> list[dict]:
    """Run morning digest for all eligible users. Called by cron every 15 min."""
    result = await db.execute(select(User))
    users = result.scalars().all()

    results = []
    for user in users:
        if not _is_digest_time(user):
            continue

        logger.info("Generating morning digest for %s (%s, tz=%s)", user.name, user.id, user.timezone)
        try:
            digest = await generate_digest(user, db)
            results.append({
                "user_id": str(user.id),
                "status": "ok",
                "preview": digest[:100],
            })
        except Exception as e:
            logger.error("Digest failed for user %s: %s", user.id, e)
            results.append({
                "user_id": str(user.id),
                "status": "error",
                "error": str(e),
            })

    return results
