import os

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user
from services.gmail_service import send_email, fetch_recent_emails

router = APIRouter(tags=["Gmail"])

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def _get_redirect_uri() -> str:
    return os.environ.get(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/gmail/callback"
    )


def _build_flow() -> Flow:
    """Build a Google OAuth flow from environment variables."""
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


@router.get("/auth/gmail")
async def gmail_auth_start(
    clerk_id: str = Query(..., description="Clerk user ID"),
    source: str = Query("web", description="Client source: 'ios' or 'web'"),
):
    """Redirect the user to Google's OAuth consent screen.

    No auth required — the frontend passes the Clerk user ID as a query
    param. The callback uses it to look up the user in the database.
    source=ios triggers a custom URL scheme redirect on callback.
    """
    flow = _build_flow()
    # Encode source into state so the callback knows where to redirect
    oauth_state = f"{clerk_id}:{source}"
    auth_url, _state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=oauth_state,
    )
    return RedirectResponse(auth_url)


@router.get("/auth/gmail/callback")
async def gmail_auth_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Exchange the authorization code for tokens and store them."""
    flow = _build_flow()
    flow.fetch_token(code=code)

    credentials = flow.credentials

    # Parse clerk_id and source from OAuth state
    parts = state.rsplit(":", 1)
    clerk_id = parts[0]
    source = parts[1] if len(parts) > 1 else "web"

    # Look up user by clerk_id passed through OAuth state, auto-create if missing
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(clerk_id=clerk_id, mode="personal", plan="free")
        db.add(user)
        await db.flush()

    user.gmail_access_token = credentials.token
    user.gmail_refresh_token = credentials.refresh_token
    user.gmail_token_expiry = credentials.expiry
    user.gmail_connected = True

    await db.commit()

    # Redirect to iOS custom scheme or web frontend
    if source == "ios":
        return RedirectResponse("axis://gmail-connected")

    frontend = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(frontend + "/settings?gmail=connected")


@router.get("/gmail/status")
async def gmail_status(user: User = Depends(get_authenticated_user)):
    """Check if Gmail is connected for the authenticated user."""
    return {"connected": bool(user.gmail_connected)}


@router.get("/gmail/inbox")
async def gmail_inbox(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return last 10 emails for ambient intelligence context."""
    if not user.gmail_connected:
        raise HTTPException(status_code=400, detail="Gmail not connected")

    emails = await fetch_recent_emails(user, db, max_results=10)
    return {"emails": emails}


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    thread_id: str | None = None
    in_reply_to: str | None = None


@router.post("/gmail/send")
async def gmail_send(
    req: SendEmailRequest,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Send an email via the user's connected Gmail account."""
    if not user.gmail_connected:
        raise HTTPException(status_code=400, detail="Gmail not connected")

    result = await send_email(
        user=user,
        db=db,
        to=req.to,
        subject=req.subject,
        body=req.body,
        thread_id=req.thread_id,
        in_reply_to=req.in_reply_to,
    )
    return {
        "status": "sent",
        "message_id": result.get("id"),
        "thread_id": result.get("threadId"),
    }
