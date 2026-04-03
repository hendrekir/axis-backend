from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from services.push_service import send_web_push


async def touch_streak(user_id, db: AsyncSession) -> dict:
    """Update the user's streak. Call on every app open / signal review."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {}

    today = date.today()
    yesterday = today - timedelta(days=1)

    if user.last_active_date == today:
        pass  # Already touched today
    elif user.last_active_date == yesterday:
        user.current_streak += 1
        if user.current_streak > user.longest_streak:
            user.longest_streak = user.current_streak
    else:
        user.current_streak = 1

    user.last_active_date = today
    await db.commit()

    return {
        "current_streak": user.current_streak,
        "longest_streak": user.longest_streak,
        "last_active_date": str(user.last_active_date),
    }


async def run_streak_reminders(db: AsyncSession) -> int:
    """Send re-engagement push to users who haven't opened today. Run at 9AM AEST."""
    today = date.today()
    result = await db.execute(
        select(User).where(
            (User.last_active_date < today) | (User.last_active_date.is_(None))
        )
    )
    users = result.scalars().all()

    count = 0
    for user in users:
        streak = user.current_streak or 0
        body = f"Your Axis streak is at risk. Signals are waiting." if streak > 1 else "You have signals waiting. Open Axis."
        await send_web_push(user.id, "Axis", body, url="/situation", db=db)
        count += 1

    return count
