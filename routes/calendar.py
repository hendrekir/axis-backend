import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user
from services.calendar_service import fetch_todays_events, fetch_upcoming_events, detect_conflicts

router = APIRouter(tags=["Calendar"])

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


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
