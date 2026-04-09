from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from database import get_db
from models import User, ThreadMessage
from routes.auth import get_authenticated_user
from services.morning_digest import generate_digest

router = APIRouter()


@router.get("/brief")
async def get_brief(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and return a morning digest / brief for the user."""
    digest = await generate_digest(user, db)
    return {"brief": digest}


@router.get("/brief/today")
async def get_brief_today(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return today's morning brief messages, generating if none exist yet."""
    try:
        user_tz = ZoneInfo(user.timezone)
    except Exception:
        user_tz = ZoneInfo("Australia/Brisbane")

    today_start = datetime.now(user_tz).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )

    # Digest messages are stored with source_skill="digest"
    result = await db.execute(
        select(ThreadMessage)
        .where(
            ThreadMessage.user_id == user.id,
            ThreadMessage.source_skill == "digest",
            ThreadMessage.created_at >= today_start,
        )
        .order_by(ThreadMessage.created_at.asc())
    )
    messages = result.scalars().all()

    if not messages:
        await generate_digest(user, db)
        result = await db.execute(
            select(ThreadMessage)
            .where(
                ThreadMessage.user_id == user.id,
                ThreadMessage.source_skill == "digest",
                ThreadMessage.created_at >= today_start,
            )
            .order_by(ThreadMessage.created_at.asc())
        )
        messages = result.scalars().all()

    return {
        "date": today_start.strftime("%Y-%m-%d"),
        "messages": [
            {
                "id": str(m.id),
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }
