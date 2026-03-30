"""
Status service — synthesises everything Axis knows about a topic.

Searches emails, tasks, notes, calendar events, and thread history,
then calls Claude to produce a structured status briefing.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Note, SentEmailsCache, Task, ThreadMessage, User
from prompts.status import STATUS_SYSTEM
from services.claude_service import generate

logger = logging.getLogger("axis.status")


async def get_status(user: User, topic: str, db: AsyncSession) -> str:
    """Assemble all data about a topic and call Claude to synthesise."""
    parts = []

    # 1. Notes mentioning the topic
    from services.notes_service import search_notes
    notes = await search_notes(user.id, topic, db, limit=5)
    if notes:
        parts.append("NOTES:\n" + "\n".join(
            f"- [{n['created_at'][:10] if n.get('created_at') else '?'}] {n['content']}"
            for n in notes
        ))

    # 2. Tasks mentioning the topic
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == user.id,
            func.lower(Task.title).contains(topic.lower()),
        )
        .order_by(Task.created_at.desc())
        .limit(5)
    )
    tasks = result.scalars().all()
    if tasks:
        parts.append("TASKS:\n" + "\n".join(
            f"- {'[DONE]' if t.is_done else '[OPEN]'} {t.title} (category: {t.category}, "
            f"{'urgent' if t.is_urgent else 'normal'})"
            for t in tasks
        ))

    # 3. Sent emails mentioning the topic
    result = await db.execute(
        select(SentEmailsCache)
        .where(
            SentEmailsCache.user_id == user.id,
            (
                func.lower(SentEmailsCache.subject).contains(topic.lower())
                | func.lower(SentEmailsCache.recipient).contains(topic.lower())
                | func.lower(SentEmailsCache.body_summary).contains(topic.lower())
            ),
        )
        .order_by(SentEmailsCache.sent_at.desc())
        .limit(5)
    )
    emails = result.scalars().all()
    if emails:
        parts.append("SENT EMAILS:\n" + "\n".join(
            f"- [{e.sent_at.strftime('%Y-%m-%d') if e.sent_at else '?'}] To: {e.recipient} "
            f"Re: {e.subject}"
            for e in emails
        ))

    # 4. Recent Gmail (if connected, fetch live)
    if user.gmail_connected:
        try:
            from services.gmail_service import fetch_recent_emails
            recent = await fetch_recent_emails(user, db, max_results=30)
            matching = [
                e for e in recent
                if topic.lower() in (e.get("subject", "") + " " + e.get("from", "") + " " + e.get("snippet", "")).lower()
            ][:5]
            if matching:
                parts.append("RECENT INBOX:\n" + "\n".join(
                    f"- From: {e['from']} | {e['subject']} | {e.get('snippet', '')[:100]}"
                    for e in matching
                ))
        except Exception as e:
            logger.warning("Gmail fetch for status failed: %s", e)

    # 5. Calendar events mentioning the topic
    if user.calendar_connected:
        try:
            from services.calendar_service import fetch_upcoming_events
            events = await fetch_upcoming_events(user, db, hours_ahead=168, max_results=20)
            matching = [
                e for e in events
                if topic.lower() in (e.get("summary", "") + " " + str(e.get("attendees", ""))).lower()
            ][:3]
            if matching:
                parts.append("CALENDAR:\n" + "\n".join(
                    f"- {e['summary']} at {e['start_dt']} ({e.get('location') or 'no location'})"
                    for e in matching
                ))
        except Exception as e:
            logger.warning("Calendar fetch for status failed: %s", e)

    # 6. Thread messages mentioning the topic
    result = await db.execute(
        select(ThreadMessage)
        .where(
            ThreadMessage.user_id == user.id,
            func.lower(ThreadMessage.content).contains(topic.lower()),
        )
        .order_by(ThreadMessage.created_at.desc())
        .limit(5)
    )
    thread_msgs = result.scalars().all()
    if thread_msgs:
        parts.append("THREAD HISTORY:\n" + "\n".join(
            f"- [{m.created_at.strftime('%Y-%m-%d') if m.created_at else '?'}] "
            f"{m.role}: {m.content[:150]}"
            for m in thread_msgs
        ))

    context_data = "\n\n".join(parts) if parts else "No data found on this topic."

    prompt = STATUS_SYSTEM.format(
        name=user.name or "there",
        topic=topic,
        context_data=context_data,
    )

    briefing = await generate(
        system_prompt="You are Axis. Return only the status briefing as plain text.",
        user_message=prompt,
        max_tokens=512,
    )

    return briefing.strip()
