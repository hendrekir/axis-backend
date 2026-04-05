from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ApiConnection, Task, ThreadMessage, User
from routes.auth import get_authenticated_user
from services.streak_service import touch_streak

router = APIRouter(tags=["User"])


class ModeEnum(str, Enum):
    personal = "personal"
    work = "work"
    builder = "builder"
    student = "student"
    founder = "founder"


class DeviceTokenIn(BaseModel):
    device_token: str


class UpdateMeRequest(BaseModel):
    mode: ModeEnum | None = None
    context_notes: str | None = None
    timezone: str | None = None


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
        "current_streak": user.current_streak or 0,
        "longest_streak": user.longest_streak or 0,
        "last_active_date": str(user.last_active_date) if user.last_active_date else None,
    }


@router.get("/me/streak")
async def get_streak(
    user: User = Depends(get_authenticated_user),
):
    return {
        "current_streak": user.current_streak or 0,
        "longest_streak": user.longest_streak or 0,
        "last_active_date": str(user.last_active_date) if user.last_active_date else None,
    }


@router.post("/me/streak/touch")
async def streak_touch(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    return await touch_streak(user.id, db)


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
    if body.timezone is not None:
        user.timezone = body.timezone
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


@router.get("/connections")
async def get_connections(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return connection status for all supported services."""
    return [
        {"provider": "Gmail", "is_connected": bool(user.gmail_connected)},
        {"provider": "Google Calendar", "is_connected": bool(user.calendar_connected)},
        {"provider": "Spotify", "is_connected": await _is_spotify_connected(user.id, db)},
        {"provider": "Stripe", "is_connected": False},
    ]


@router.post("/me/device-token")
async def store_device_token(
    body: DeviceTokenIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Store an APNs device token for push notifications."""
    user.apns_token = body.device_token
    await db.commit()
    return {"status": "registered", "device_token": body.device_token}


@router.get("/me/widget-data")
async def get_widget_data(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Lightweight endpoint for WidgetKit — signal, MIT count, next event."""
    # Top signal: latest assistant intel message (not archived)
    signal_result = await db.execute(
        select(ThreadMessage.content)
        .where(
            ThreadMessage.user_id == user.id,
            ThreadMessage.role == "assistant",
            ThreadMessage.message_type == "intel",
            ThreadMessage.archived == False,
        )
        .order_by(ThreadMessage.created_at.desc())
        .limit(1)
    )
    signal = signal_result.scalar_one_or_none()

    # MIT count: incomplete urgent tasks
    mit_result = await db.execute(
        select(func.count())
        .select_from(Task)
        .where(Task.user_id == user.id, Task.is_done == False, Task.is_urgent == True)
    )
    mit_count = mit_result.scalar() or 0

    # Next event (lightweight — only if calendar connected)
    next_event = None
    if user.calendar_connected:
        from services.calendar_service import get_next_event
        try:
            evt = await get_next_event(user, db)
            if evt:
                next_event = {"title": evt["summary"], "time": evt["start_dt"]}
        except Exception:
            pass  # Don't fail widget data over calendar errors

    return {
        "signal": signal[:200] if signal else None,
        "mit_count": mit_count,
        "next_event": next_event,
    }
