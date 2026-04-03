import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Task, Interaction
from routes.auth import get_authenticated_user

logger = logging.getLogger("axis.insights")

router = APIRouter()


@router.get("/me/insights")
async def get_insights(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return contextual insight strings based on user's connected data."""
    insights = []

    # Task completion rate this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(func.count()).where(
            Task.user_id == user.id,
            Task.created_at >= week_ago,
        )
    )
    total_tasks = result.scalar() or 0

    result = await db.execute(
        select(func.count()).where(
            Task.user_id == user.id,
            Task.is_done == True,
            Task.created_at >= week_ago,
        )
    )
    done_tasks = result.scalar() or 0

    if total_tasks > 0:
        rate = round(done_tasks / total_tasks * 100)
        insights.append(f"Task completion rate this week: {rate}% ({done_tasks}/{total_tasks})")

    # Brain dump usage
    result = await db.execute(
        select(func.count()).where(
            Interaction.user_id == user.id,
            Interaction.content_type == "brain_dump",
            Interaction.created_at >= week_ago,
        )
    )
    dumps = result.scalar() or 0
    if dumps > 0:
        insights.append(f"You ran {dumps} brain dump{'s' if dumps != 1 else ''} this week.")

    # Streak context
    if user.current_streak and user.current_streak >= 3:
        insights.append(f"You're on a {user.current_streak}-day streak. Your longest is {user.longest_streak}.")

    # Calendar insight (if connected)
    if user.calendar_connected:
        insights.append("Calendar connected — Axis is tracking your schedule.")

    # Gmail insight (if connected)
    if user.gmail_connected:
        insights.append("Gmail connected — Axis is reading your inbox.")

    # Static fallback
    if not insights:
        insights.append("Connect Gmail or Calendar for richer insights.")

    return {"insights": insights}
