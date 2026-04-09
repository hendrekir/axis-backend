import json
import logging
import re
from datetime import date, datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("axis.me")

from database import get_db
from models import (
    ApiConnection,
    DispatchedSignal,
    JournalEntry,
    Recommendation,
    Task,
    ThreadMessage,
    User,
)
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


def _idle_response() -> dict:
    return {
        "state": "idle",
        "title": "Axis is watching",
        "subtitle": "Tap to capture",
        "icon": "eye.fill",
        "urgency": 0,
        "primary_action": "capture",
        "secondary_action": None,
        "signal_id": None,
        "event_id": None,
        "destination": None,
    }


def _row_to_response(row: DispatchedSignal, *, state: str, icon: str,
                     primary_action: str, secondary_action: str,
                     title: str | None = None, subtitle: str | None = None) -> dict:
    return {
        "state": state,
        "title": title if title is not None else (row.title or ""),
        "subtitle": subtitle if subtitle is not None else (row.subtitle or ""),
        "icon": icon,
        "urgency": row.urgency or 0,
        "primary_action": primary_action,
        "secondary_action": secondary_action,
        "signal_id": str(row.id),
        "event_id": row.event_id,
        "destination": row.destination,
    }


@router.get("/me/widget-data")
async def get_widget_data(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """7-state lock-screen widget priority resolver. DB-only. <200ms."""
    now = datetime.utcnow()
    fresh_cutoff = now - timedelta(hours=48)

    not_handled = and_(
        DispatchedSignal.completed == False,
        DispatchedSignal.dismissed == False,
        or_(DispatchedSignal.snoozed_until.is_(None), DispatchedSignal.snoozed_until <= now),
    )

    # 1. departure_alert — most recent travel_time signal in the last 30 min
    depart_cutoff = now - timedelta(minutes=30)
    res = await db.execute(
        select(DispatchedSignal)
        .where(
            DispatchedSignal.user_id == user.id,
            DispatchedSignal.action_type == "open_maps",
            DispatchedSignal.dispatched_at >= depart_cutoff,
            not_handled,
        )
        .order_by(DispatchedSignal.dispatched_at.desc())
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if row:
        return _row_to_response(
            row,
            state="departure_alert",
            icon="car.fill",
            primary_action="open_maps",
            secondary_action="got_it",
        )

    # 2. now_signal — urgency >= 8, not dispatched in last 15 min (i.e. settled)
    fifteen_ago = now - timedelta(minutes=15)
    res = await db.execute(
        select(DispatchedSignal)
        .where(
            DispatchedSignal.user_id == user.id,
            DispatchedSignal.urgency >= 8,
            DispatchedSignal.dispatched_at >= fresh_cutoff,
            DispatchedSignal.dispatched_at <= fifteen_ago,
            or_(DispatchedSignal.action_type.is_(None), DispatchedSignal.action_type != "open_maps"),
            or_(DispatchedSignal.action_type.is_(None), DispatchedSignal.action_type != "silence"),
            not_handled,
        )
        .order_by(DispatchedSignal.urgency.desc(), DispatchedSignal.dispatched_at.desc())
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if row:
        return _row_to_response(
            row,
            state="now_signal",
            icon="exclamationmark.circle.fill",
            primary_action="handle",
            secondary_action="snooze_2h",
        )

    # 3. meeting_prep — calendar event 25-35 min out with attendees
    res = await db.execute(
        select(DispatchedSignal)
        .where(
            DispatchedSignal.user_id == user.id,
            DispatchedSignal.action_type == "meeting_prep",
            DispatchedSignal.dispatched_at >= fresh_cutoff,
            not_handled,
        )
        .order_by(DispatchedSignal.dispatched_at.desc())
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if row:
        return _row_to_response(
            row,
            state="meeting_prep",
            icon="calendar",
            primary_action="read_brief",
            secondary_action="dismiss",
        )

    # 4. silence_detected
    res = await db.execute(
        select(DispatchedSignal)
        .where(
            DispatchedSignal.user_id == user.id,
            DispatchedSignal.action_type == "silence",
            DispatchedSignal.dismissed == False,
        )
        .order_by(DispatchedSignal.dispatched_at.desc())
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if row:
        return _row_to_response(
            row,
            state="silence_detected",
            icon="waveform",
            primary_action="follow_up",
            secondary_action="remind_3d",
        )

    # 5. today_signal — urgency 5-7
    res = await db.execute(
        select(DispatchedSignal)
        .where(
            DispatchedSignal.user_id == user.id,
            DispatchedSignal.urgency >= 5,
            DispatchedSignal.urgency <= 7,
            DispatchedSignal.dispatched_at >= fresh_cutoff,
            not_handled,
        )
        .order_by(DispatchedSignal.urgency.desc(), DispatchedSignal.dispatched_at.desc())
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if row:
        return _row_to_response(
            row,
            state="today_signal",
            icon="bell.fill",
            primary_action="reply",
            secondary_action="later",
        )

    # 6. morning_brief — within 2 hours of wake_time, not yet read today
    try:
        tz = ZoneInfo(user.timezone or "Australia/Brisbane")
    except Exception:
        tz = ZoneInfo("UTC")
    local_now = datetime.now(tz)
    wake_str = (user.wake_time or "07:00").strip()
    try:
        wh, wm = (int(x) for x in wake_str.split(":")[:2])
    except Exception:
        wh, wm = 7, 0
    wake_dt = local_now.replace(hour=wh, minute=wm, second=0, microsecond=0)
    brief_window_end = wake_dt + timedelta(hours=2)
    brief_already_read = (
        user.last_brief_read_date is not None
        and user.last_brief_read_date == local_now.date()
    )
    if wake_dt <= local_now <= brief_window_end and not brief_already_read:
        # Count signals caught in the last ~12 hours for the brief headline
        twelve_ago = now - timedelta(hours=12)
        count_res = await db.execute(
            select(func.count())
            .select_from(DispatchedSignal)
            .where(
                DispatchedSignal.user_id == user.id,
                DispatchedSignal.dispatched_at >= twelve_ago,
            )
        )
        caught = count_res.scalar() or 0
        return {
            "state": "morning_brief",
            "title": "Your Axis brief",
            "subtitle": f"{caught} things caught · 2 min",
            "icon": "sun.max.fill",
            "urgency": 5,
            "primary_action": "play",
            "secondary_action": "open",
            "signal_id": None,
            "event_id": None,
            "destination": None,
        }

    # 7. idle
    return _idle_response()


RECOMMENDATION_SYSTEM = """You are a personal researcher. Based on this person's context — their notes, recent journal entries, and what they're thinking about — recommend ONE thing to read, watch, or listen to today.

It must be a real, specific, existing piece of content. Not generic. Relevant to their life this week.

Return ONLY valid JSON:
{"type": "podcast|article|book", "title": "exact title", "reason": "one sentence why this is relevant to them right now", "url": "real URL", "source": "where to find it"}"""


@router.get("/me/recommendation")
async def get_recommendation(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """One personalised recommendation per day, cached."""
    today = date.today()

    # Check cache
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.user_id == user.id,
            Recommendation.date == today,
        )
    )
    cached = result.scalar_one_or_none()
    if cached:
        return cached.recommendation

    # Build context from user notes + recent journal
    parts = []
    if user.context_notes:
        parts.append(f"About this person:\n{user.context_notes}")

    journal_result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(3)
    )
    entries = journal_result.scalars().all()
    if entries:
        journal_text = "\n".join(
            f"- Q: {e.question}\n  A: {e.answer}" for e in entries
        )
        parts.append(f"Recent journal:\n{journal_text}")

    if not parts:
        parts.append("No context available yet — recommend something broadly useful for personal growth.")

    context = "\n\n".join(parts)

    # Call Perplexity (via model_router, falls back to Claude)
    from services.model_router import route
    raw_result = await route(
        task_type="discovery",
        system=RECOMMENDATION_SYSTEM,
        user_msg=context,
        max_tokens=512,
    )

    # Parse JSON
    raw_text = raw_result["text"]
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw_text.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    try:
        rec = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Recommendation parse failed for user %s: %s", user.id, raw_text[:200])
        rec = {
            "type": "article",
            "title": "Could not generate recommendation",
            "reason": "Try again tomorrow — Axis needs more context.",
            "url": "",
            "source": "",
        }

    # Cache
    db.add(Recommendation(
        user_id=user.id,
        date=today,
        recommendation=rec,
    ))
    await db.commit()

    return rec
