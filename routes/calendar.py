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

    try:
        events = await fetch_upcoming_events(user, db, hours_ahead=hours)
    except Exception as e:
        error_msg = str(e).lower()
        if "invalid_grant" in error_msg or "token" in error_msg and ("expired" in error_msg or "revoked" in error_msg):
            user.calendar_connected = False
            await db.commit()
            logger.warning("Calendar token revoked for user %s — disconnected", user.id)
            raise HTTPException(status_code=401, detail="Calendar token expired — please reconnect")
        logger.error("Calendar fetch failed for user %s: %s", user.id, e)
        raise HTTPException(status_code=502, detail="Failed to fetch calendar events")
    return {"events": events}


@router.get("/calendar/meeting-prep/{event_id}")
async def get_meeting_prep(
    event_id: str = Path(..., description="Google Calendar event ID"),
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a full meeting prep brief for a specific calendar event.

    Pulls Gmail threads, relationship graph data, Perplexity web context,
    and synthesises via Claude into a structured brief.
    """
    if not user.calendar_connected:
        raise HTTPException(status_code=400, detail="Calendar not connected")

    creds = await refresh_if_needed(user, db)
    if creds is None:
        raise HTTPException(status_code=400, detail="Calendar credentials invalid")

    service = build("calendar", "v3", credentials=creds)
    try:
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Event not found")

    # Normalise event
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

    attendee_emails = {a["email"].lower() for a in attendees if a["email"]}

    # --- 1. Gmail threads per attendee (last 5 matching any attendee) ---
    threads_by_email: dict[str, list[dict]] = {e: [] for e in attendee_emails}
    all_email_threads: list[dict] = []
    if user.gmail_connected and attendee_emails:
        from services.gmail_service import fetch_recent_emails
        try:
            emails = await fetch_recent_emails(user, db, max_results=50)
            for e in emails:
                sender = (e.get("from") or "").lower()
                thread = {
                    "from": e.get("from", ""),
                    "subject": e.get("subject", ""),
                    "snippet": e.get("snippet", "")[:200],
                    "date": e.get("date", ""),
                }
                for addr in attendee_emails:
                    if addr in sender and len(threads_by_email[addr]) < 5:
                        threads_by_email[addr].append(thread)
                if len(all_email_threads) < 5 and any(addr in sender for addr in attendee_emails):
                    all_email_threads.append(thread)
        except Exception as exc:
            logger.warning("Gmail fetch for meeting prep failed: %s", exc)

    # --- 2. Person profiles per attendee ---
    from models import PersonProfile
    pp_result = await db.execute(
        select(PersonProfile).where(
            PersonProfile.user_id == user.id,
            PersonProfile.contact_email.in_(list(attendee_emails)),
        )
    )
    profiles_by_email = {p.contact_email.lower(): p for p in pp_result.scalars().all()}

    # --- 3. Perplexity web context per attendee (parallel) ---
    from services.perplexity_service import person_lookup

    async def _web_lookup(attendee: dict) -> dict:
        name = attendee.get("name") or attendee.get("email", "")
        email = attendee.get("email", "")
        company = email.split("@")[1].split(".")[0] if "@" in email else ""
        query_name = (
            f"{name} {company}".strip()
            if company and company not in ("gmail", "yahoo", "hotmail", "outlook", "icloud")
            else name
        )
        if not query_name:
            return {**attendee, "web_context": None}
        try:
            result = await person_lookup(
                query_name,
                context=f"Meeting: {event_data['summary']}",
            )
            return {**attendee, "web_context": result["text"]}
        except Exception:
            return {**attendee, "web_context": None}

    if attendees:
        web_results = await asyncio.gather(*[_web_lookup(a) for a in attendees[:5]])
    else:
        web_results = []

    # --- 4. Assemble per-attendee data ---
    attendees_enriched = []
    for a in web_results:
        email_lower = a["email"].lower()
        profile = profiles_by_email.get(email_lower)
        last_threads = threads_by_email.get(email_lower, [])
        attendees_enriched.append({
            "name": a.get("name", ""),
            "email": a["email"],
            "last_thread": last_threads[0] if last_threads else None,
            "profile": {
                "contact_name": profile.contact_name if profile else None,
                "avg_response_time_hours": profile.avg_response_time_hours if profile else None,
                "typical_communication_style": profile.typical_communication_style if profile else None,
                "last_contact_date": profile.last_contact_date.isoformat() if profile and profile.last_contact_date else None,
                "silence_baseline_days": profile.silence_baseline_days if profile else None,
                "notes": profile.notes if profile else None,
            } if profile else None,
            "web_context": a.get("web_context"),
        })

    # --- 5. Claude synthesis ---
    from services.claude_service import generate as claude_gen
    import json
    import re

    email_summary = "\n".join(
        f"- {e['from']}: {e['subject']} — {e['snippet']}" for e in all_email_threads
    ) or "No recent email history with attendees."

    attendee_context = "\n".join(
        f"- {a['name'] or a['email']}: "
        f"Web: {a.get('web_context') or 'Unknown'}. "
        f"Profile: {a['profile']['typical_communication_style'] or 'no data'}, "
        f"last contact {a['profile']['last_contact_date'] or 'never'}"
        f"{', notes: ' + a['profile']['notes'] if a['profile'] and a['profile']['notes'] else ''}"
        if a.get("profile") else
        f"- {a['name'] or a['email']}: Web: {a.get('web_context') or 'Unknown'}. No profile data."
        for a in attendees_enriched
    ) or "No attendees listed."

    brief_raw = await claude_gen(
        system_prompt=(
            "You are Axis, preparing a meeting brief. Return valid JSON only, no markdown fences.\n"
            'Format: {"who_they_are": "...", "last_discussed": "...", '
            '"what_they_care_about": "...", "watch_for": ["item 1", "item 2", ...]}'
        ),
        user_message=(
            f"Meeting: {event_data['summary']}\n"
            f"Time: {event_data['start_dt']}\n"
            f"Location: {event_data['location'] or 'Not specified'}\n"
            f"Description: {event_data['description'] or 'None'}\n\n"
            f"Attendees with context:\n{attendee_context}\n\n"
            f"Recent email threads with attendees:\n{email_summary}\n\n"
            "Synthesise: who they are, what you last discussed, what they care about, watch-fors."
        ),
        max_tokens=768,
    )

    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', brief_raw.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)
    try:
        brief_parsed = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        brief_parsed = {
            "who_they_are": cleaned,
            "last_discussed": "",
            "what_they_care_about": "",
            "watch_for": [],
        }

    return {
        "event": event_data,
        "attendees": attendees_enriched,
        "brief_text": brief_parsed,
        "web_context": [
            {"name": a["name"] or a["email"], "context": a.get("web_context")}
            for a in attendees_enriched
            if a.get("web_context")
        ],
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
