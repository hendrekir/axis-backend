import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user

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
async def gmail_auth_start(request: Request, user: User = Depends(get_authenticated_user)):
    """Redirect the user to Google's OAuth consent screen."""
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=str(user.id),
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

    # Look up user by ID passed through OAuth state
    user = await db.get(User, state)
    if user is None:
        return RedirectResponse(
            os.environ.get("APP_URL", "/") + "?gmail=error&reason=user_not_found"
        )

    user.gmail_access_token = credentials.token
    user.gmail_refresh_token = credentials.refresh_token
    user.gmail_token_expiry = credentials.expiry
    user.gmail_connected = True

    await db.commit()

    # Redirect back to the app with success indicator
    return RedirectResponse(os.environ.get("APP_URL", "/") + "?gmail=connected")
