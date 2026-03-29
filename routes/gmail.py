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
from services.gmail_service import send_email

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
):
    """Redirect the user to Google's OAuth consent screen.

    No auth required — the frontend passes the Clerk user ID as a query
    param. The callback uses it to look up the user in the database.
    """
    flow = _build_flow()
    auth_url, _state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=clerk_id,
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

    # Look up user by clerk_id passed through OAuth state, auto-create if missing
    result = await db.execute(select(User).where(User.clerk_id == state))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(clerk_id=state, mode="personal", plan="free")
        db.add(user)
        await db.flush()

    user.gmail_access_token = credentials.token
    user.gmail_refresh_token = credentials.refresh_token
    user.gmail_token_expiry = credentials.expiry
    user.gmail_connected = True

    await db.commit()

    # Redirect back to the frontend settings page
    frontend = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(frontend + "/settings?gmail=connected")


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
