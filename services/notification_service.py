"""
Notification service — time-based pushes using per-user timezone.

Called from run_dispatch() on every 15-minute cycle. Each function checks
whether it's the right local hour for each user before sending.
"""

import logging
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from models import User
from services.push_service import send_web_push

logger = logging.getLogger("axis.notifications")

JOURNAL_QUESTIONS = {
    0: "What's the one thing that would make this week a win?",
    1: "What are you avoiding right now, and why?",
    2: "Who do you need to reach out to that you've been putting off?",
    3: "What decision are you sitting on that needs to be made?",
    4: "What's one thing you learned or noticed this week?",
    5: "What drained you this week? What energised you?",
    6: "What do you want to be different next week?",
}


def _user_local_hour(user: User) -> tuple[int, int]:
    """Return (hour, minute) in the user's local timezone."""
    tz_str = user.timezone or "UTC"
    try:
        tz = ZoneInfo(tz_str)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    return now.hour, now.minute


async def send_journal_prompts(db: AsyncSession) -> int:
    """Send 8PM local-time journal push to eligible users."""
    result = await db.execute(select(User))
    users = result.scalars().all()

    count = 0
    for user in users:
        hour, minute = _user_local_hour(user)
        if hour == 20 and minute < 15:
            weekday = datetime.now(ZoneInfo(user.timezone or "UTC")).weekday()
            question = JOURNAL_QUESTIONS.get(weekday, "What's on your mind?")
            await send_web_push(
                user.id, "Axis", f"One question for today: {question}",
                url="/mind", db=db,
            )
            count += 1

    if count > 0:
        logger.info("Journal prompts sent to %d users", count)
    return count


async def send_streak_reminders(db: AsyncSession) -> int:
    """Send 9AM local-time streak reminder to users who haven't opened today."""
    today = date.today()
    result = await db.execute(
        select(User).where(
            (User.last_active_date < today) | (User.last_active_date.is_(None))
        )
    )
    users = result.scalars().all()

    count = 0
    for user in users:
        hour, minute = _user_local_hour(user)
        if hour == 9 and minute < 15:
            streak = user.current_streak or 0
            days_inactive = (today - user.last_active_date).days if user.last_active_date else 99
            if days_inactive >= 2:
                body = "Axis is working with less context. One question takes 30 seconds."
                url = "/mind"
            elif streak > 1:
                body = "Your Axis streak is at risk. Signals are waiting."
                url = "/situation"
            else:
                body = "You have signals waiting. Open Axis."
                url = "/situation"
            await send_web_push(user.id, "Axis", body, url=url, db=db)
            count += 1

    if count > 0:
        logger.info("Streak reminders sent to %d users", count)
    return count
