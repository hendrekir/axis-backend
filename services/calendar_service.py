"""
Google Calendar service — fetch events, detect conflicts, support meeting prep.
"""

import logging
import os
from datetime import datetime, timedelta

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from models import User

logger = logging.getLogger("axis.calendar")

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials(user: User) -> Credentials | None:
    """Build Google credentials from stored calendar tokens."""
    if not user.calendar_access_token:
        return None

    creds = Credentials(
        token=user.calendar_access_token,
        refresh_token=user.calendar_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )

    if creds.expiry:
        creds.expiry = user.calendar_token_expiry

    return creds


async def refresh_if_needed(user: User, db: AsyncSession) -> Credentials | None:
    """Return valid credentials, refreshing if expired."""
    creds = _get_credentials(user)
    if creds is None:
        return None

    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        user.calendar_access_token = creds.token
        user.calendar_token_expiry = creds.expiry
        await db.commit()

    return creds


async def fetch_todays_events(user: User, db: AsyncSession) -> list[dict]:
    """Fetch today's calendar events."""
    creds = await refresh_if_needed(user, db)
    if creds is None:
        return []

    service = build("calendar", "v3", credentials=creds)

    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    results = service.events().list(
        calendarId="primary",
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()

    return [_format_event(e) for e in results.get("items", [])]


async def fetch_upcoming_events(
    user: User, db: AsyncSession, hours_ahead: int = 24, max_results: int = 10
) -> list[dict]:
    """Fetch events in the next N hours."""
    creds = await refresh_if_needed(user, db)
    if creds is None:
        return []

    service = build("calendar", "v3", credentials=creds)

    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(hours=hours_ahead)).isoformat() + "Z"

    results = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=max_results,
    ).execute()

    return [_format_event(e) for e in results.get("items", [])]


async def get_next_event(user: User, db: AsyncSession) -> dict | None:
    """Get the single next upcoming event."""
    events = await fetch_upcoming_events(user, db, hours_ahead=12, max_results=1)
    return events[0] if events else None


def detect_conflicts(events: list[dict]) -> list[dict]:
    """Find overlapping events."""
    conflicts = []
    sorted_events = sorted(events, key=lambda e: e.get("start_dt", ""))

    for i in range(len(sorted_events) - 1):
        curr_end = sorted_events[i].get("end_dt", "")
        next_start = sorted_events[i + 1].get("start_dt", "")
        if curr_end and next_start and curr_end > next_start:
            conflicts.append({
                "event_a": sorted_events[i]["summary"],
                "event_b": sorted_events[i + 1]["summary"],
                "overlap_start": next_start,
                "overlap_end": min(curr_end, sorted_events[i + 1].get("end_dt", curr_end)),
            })

    return conflicts


def _format_event(event: dict) -> dict:
    """Normalise a Google Calendar event into a clean dict."""
    start = event.get("start", {})
    end = event.get("end", {})
    start_dt = start.get("dateTime", start.get("date", ""))
    end_dt = end.get("dateTime", end.get("date", ""))

    attendees = event.get("attendees", [])

    return {
        "id": event.get("id", ""),
        "summary": event.get("summary", "(No title)"),
        "start_dt": start_dt,
        "end_dt": end_dt,
        "location": event.get("location", ""),
        "description": (event.get("description") or "")[:200],
        "attendees": [
            {"email": a.get("email", ""), "name": a.get("displayName", "")}
            for a in attendees[:10]
        ],
        "attendee_count": len(attendees),
        "meet_link": event.get("hangoutLink", ""),
        "is_all_day": "date" in start and "dateTime" not in start,
    }


async def create_calendar_event(
    user: User,
    db: AsyncSession,
    summary: str,
    start: datetime,
    end: datetime,
    attendee: str | None = None,
    location: str | None = None,
    description: str | None = None,
) -> dict:
    """Create a Google Calendar event. Returns dict with event_id, title, start_dt, html_link."""
    creds = await refresh_if_needed(user, db)
    if creds is None:
        raise ValueError("Google Calendar not connected")

    service = build("calendar", "v3", credentials=creds)

    tz = user.timezone or "Australia/Brisbane"
    event_body = {
        "summary": summary,
        "start": {"dateTime": start.isoformat(), "timeZone": tz},
        "end": {"dateTime": end.isoformat(), "timeZone": tz},
    }

    if attendee:
        event_body["attendees"] = [{"email": attendee}] if "@" in attendee else []
    if location:
        event_body["location"] = location
    if description:
        event_body["description"] = description

    result = service.events().insert(calendarId="primary", body=event_body).execute()
    return {
        "event_id": result.get("id"),
        "title": summary,
        "start_dt": start.isoformat(),
        "html_link": result.get("htmlLink"),
    }
