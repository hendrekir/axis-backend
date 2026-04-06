import asyncio
import logging
import os

from datetime import datetime as dt_datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user
from services.calendar_service import (
    create_calendar_event, fetch_todays_events, fetch_upcoming_events,
    detect_conflicts, refresh_if_needed,
)

logger = logging.getLogger("axis.calendar.routes")

router = APIRouter(tags=["Calendar"])

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_redirect_uri() -> str:
    return os.environ.get(
        "GOOGLE_CALENDAR_REDIRECT_URI",
        os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/calendar/callback").replace(
            "/auth/gmail/callback", "/auth/calendar/callback"
        ),
    )


def _build_flow() -> Flow:
    """Build a Google OAuth flow for Calendar."""
    client_config = {
        "web": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = _get_redirect_uri()
    return flow


@router.get("/auth/calendar")
async def calendar_auth_start(
    clerk_id: str = Query(..., description="Clerk user ID"),
):
    """Redirect to Google OAuth consent for Calendar access."""
    flow = _build_flow()
    auth_url, _state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=clerk_id,
    )
    return RedirectResponse(auth_url)


@router.get("/auth/calendar/callback")
async def calendar_auth_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Exchange authorization code for Calendar tokens."""
    flow = _build_flow()
    flow.fetch_token(code=code)

    credentials = flow.credentials

    result = await db.execute(select(User).where(User.clerk_id == state))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(clerk_id=state, mode="personal", plan="free")
        db.add(user)
        await db.flush()

    user.calendar_access_token = credentials.token
    user.calendar_refresh_token = credentials.refresh_token
    user.calendar_token_expiry = credentials.expiry
    user.calendar_connected = True

    await db.commit()

    frontend = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(frontend + "/settings?calendar=connected")


@router.get("/calendar/today")
async def get_today(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return today's calendar events."""
    if not user.calendar_connected:
        raise HTTPException(status_code=400, detail="Calendar not connected")

    events = await fetch_todays_events(user, db)
    conflicts = detect_conflicts(events)
    return {"events": events, "conflicts": conflicts}


@router.get("/calendar/upcoming")
async def get_upcoming(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    hours: int = Query(24, ge=1, le=72),
):
    """Return upcoming events in the next N hours."""
    if not user.calendar_connected:
        raise HTTPException(status_code=400, detail="Calendar not connected")

    events = await fetch_upcoming_events(user, db, hours_ahead=hours)
    return {"events": events}


@router.get("/calendar/meeting-prep/{event_id}")
async def get_meeting_prep(
    event_id: str = Path(..., description="Google Calendar event ID"),
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a meeting prep brief for a specific calendar event."""
    if not user.calendar_connected:
        raise HTTPException(status_code=400, detail="Calendar not connected")

    # Fetch the specific event from Google Calendar
    creds = await refresh_if_needed(user, db)
    if creds is None:
        raise HTTPException(status_code=400, detail="Calendar credentials invalid")

    service = build("calendar", "v3", credentials=creds)
    try:
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Event not found")

    # Normalise event data
    start = event.get("start", {})
    end = event.get("end", {})
    attendees_raw = event.get("attendees", [])
    attendees = [
        {"email": a.get("email", ""), "name": a.get("displayName", "")}
        for a in attendees_raw[:10]
    ]

    event_data = {
        "id": event.get("id", ""),
        "summary": event.get("summary", "(No title)"),
        "start_dt": start.get("dateTime", start.get("date", "")),
        "end_dt": end.get("dateTime", end.get("date", "")),
        "location": event.get("location", ""),
        "description": (event.get("description") or "")[:500],
        "attendees": attendees,
        "meet_link": event.get("hangoutLink", ""),
    }

    # Fetch recent emails with attendees (if Gmail connected)
    email_context = []
    if user.gmail_connected and attendees:
        from services.gmail_service import fetch_recent_emails
        try:
            emails = await fetch_recent_emails(user, db, max_results=50)
            attendee_emails = {a["email"].lower() for a in attendees if a["email"]}
            for e in emails:
                sender = (e.get("from") or "").lower()
                if any(addr in sender for addr in attendee_emails):
                    email_context.append({
                        "from": e.get("from", ""),
                        "subject": e.get("subject", ""),
                        "snippet": e.get("snippet", "")[:200],
                        "date": e.get("date", ""),
                    })
            email_context = email_context[:5]
        except Exception as exc:
            logger.warning("Failed to fetch emails for meeting prep: %s", exc)

    # Research each attendee via Perplexity (fall back to Claude)
    attendees_with_context = []

    async def _lookup_attendee(attendee: dict) -> dict:
        name = attendee.get("name") or attendee.get("email", "")
        if not name:
            return {**attendee, "context": None}
        try:
            from services.perplexity_service import person_lookup
            result = await person_lookup(
                name, context=f"Meeting: {event_data['summary']}"
            )
            return {**attendee, "context": result["text"]}
        except Exception:
            try:
                from services.claude_service import generate as claude_gen
                text = await claude_gen(
                    system_prompt="Provide brief professional context based on the name and email domain. 2-3 sentences. If unknown, say so.",
                    user_message=f"Who is {name} ({attendee.get('email', '')})?",
                    max_tokens=200,
                )
                return {**attendee, "context": text}
            except Exception:
                return {**attendee, "context": None}

    if attendees:
        tasks = [_lookup_attendee(a) for a in attendees[:5]]
        attendees_with_context = await asyncio.gather(*tasks)
    else:
        attendees_with_context = []

    # Generate key points and watch-for via Claude
    from services.claude_service import generate as claude_gen

    email_summary = "\n".join(
        f"- {e['from']}: {e['subject']} — {e['snippet']}"
        for e in email_context
    ) if email_context else "No recent email history with attendees."

    attendee_summary = "\n".join(
        f"- {a.get('name') or a['email']}: {a.get('context') or 'No info available'}"
        for a in attendees_with_context
    ) if attendees_with_context else "No attendees listed."

    analysis = await claude_gen(
        system_prompt=(
            "You are Axis, preparing a meeting brief. Return valid JSON only, no markdown fences. "
            'Format: {"key_points": ["point 1", "point 2", ...], "watch_for": ["item 1", "item 2", ...]}'
        ),
        user_message=(
            f"Meeting: {event_data['summary']}\n"
            f"Time: {event_data['start_dt']}\n"
            f"Location: {event_data['location'] or 'Not specified'}\n"
            f"Description: {event_data['description'] or 'None'}\n\n"
            f"Attendees:\n{attendee_summary}\n\n"
            f"Recent emails with attendees:\n{email_summary}\n\n"
            "Generate 3-5 key points to prepare for this meeting and 2-3 things to watch for."
        ),
        max_tokens=512,
    )

    # Parse Claude's JSON response
    import json
    try:
        parsed = json.loads(analysis)
        key_points = parsed.get("key_points", [])
        watch_for = parsed.get("watch_for", [])
    except (json.JSONDecodeError, TypeError):
        key_points = [analysis]
        watch_for = []

    return {
        "event": event_data,
        "attendees_with_context": [
            {
                "email": a.get("email", ""),
                "name": a.get("name", ""),
                "context": a.get("context"),
            }
            for a in attendees_with_context
        ],
        "email_context": email_context,
        "key_points": key_points,
        "watch_for": watch_for,
    }


class CreateEventIn(BaseModel):
    title: str
    start_dt: str
    end_dt: str
    location: str | None = None
    description: str | None = None


@router.post("/calendar/create")
async def create_event(
    body: CreateEventIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Google Calendar event."""
    if not user.calendar_connected:
        raise HTTPException(status_code=400, detail="Calendar not connected")

    start = dt_datetime.fromisoformat(body.start_dt)
    end = dt_datetime.fromisoformat(body.end_dt)

    result = await create_calendar_event(
        user=user,
        db=db,
        summary=body.title,
        start=start,
        end=end,
        location=body.location,
        description=body.description,
    )

    return result
