from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ApiConnection, User
from routes.auth import get_authenticated_user

router = APIRouter(tags=["User"])


class ModeEnum(str, Enum):
    personal = "personal"
    work = "work"
    builder = "builder"
    student = "student"
    founder = "founder"


class UpdateMeRequest(BaseModel):
    mode: ModeEnum | None = None
    context_notes: str | None = None


async def _is_spotify_connected(user_id, db: AsyncSession) -> bool:
    result = await db.execute(
        select(ApiConnection.is_connected).where(
            ApiConnection.user_id == user_id,
            ApiConnection.service == "spotify",
        )
    )
    row = result.scalar_one_or_none()
    return bool(row)


@router.get("/me")
async def get_me(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's profile."""
    return {
        "id": str(user.id),
        "name": user.name,
        "mode": user.mode,
        "timezone": user.timezone,
        "plan": user.plan,
        "gmail_connected": user.gmail_connected,
        "calendar_connected": user.calendar_connected,
        "spotify_connected": await _is_spotify_connected(user.id, db),
        "context_notes": user.context_notes or "",
    }


@router.patch("/me")
async def update_me(
    body: UpdateMeRequest,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile."""
    if body.mode is not None:
        user.mode = body.mode.value
    if body.context_notes is not None:
        user.context_notes = body.context_notes
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {
        "id": str(user.id),
        "name": user.name,
        "mode": user.mode,
        "timezone": user.timezone,
        "plan": user.plan,
        "gmail_connected": user.gmail_connected,
        "calendar_connected": user.calendar_connected,
        "spotify_connected": await _is_spotify_connected(user.id, db),
        "context_notes": user.context_notes or "",
    }
