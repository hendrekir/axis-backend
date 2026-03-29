"""
Spotify OAuth + data routes.

OAuth flow:
  GET /auth/spotify?clerk_id=...  → redirect to Spotify consent
  GET /auth/spotify/callback      → exchange code, store tokens in api_connections

Data endpoints (require auth):
  GET /spotify/recent             → recently played tracks
  GET /spotify/new-releases       → new releases from followed artists
"""

import os
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ApiConnection, User
from routes.auth import get_authenticated_user

router = APIRouter(tags=["Spotify"])

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.environ.get(
    "SPOTIFY_REDIRECT_URI", "http://localhost:8000/auth/spotify/callback"
)

SCOPES = "user-read-recently-played user-follow-read user-library-read user-top-read user-read-private"
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------


@router.get("/auth/spotify")
async def spotify_auth_start(
    clerk_id: str = Query(..., description="Clerk user ID"),
):
    """Redirect to Spotify OAuth consent screen."""
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
        "state": clerk_id,
        "show_dialog": "true",
    }
    url = f"{AUTHORIZE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return RedirectResponse(url)


@router.get("/auth/spotify/callback")
async def spotify_auth_callback(
    request: Request,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Exchange authorization code for tokens and store in api_connections."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": SPOTIFY_REDIRECT_URI,
                "client_id": SPOTIFY_CLIENT_ID,
                "client_secret": SPOTIFY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Spotify token exchange failed: {resp.text}")
        tokens = resp.json()

    # Look up user by clerk_id, auto-create if missing
    result = await db.execute(select(User).where(User.clerk_id == state))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(clerk_id=state, mode="personal", plan="free")
        db.add(user)
        await db.flush()

    # Upsert api_connections row
    result = await db.execute(
        select(ApiConnection).where(
            ApiConnection.user_id == user.id,
            ApiConnection.service == "spotify",
        )
    )
    conn = result.scalar_one_or_none()

    expires_in = tokens.get("expires_in", 3600)
    expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    if conn is None:
        conn = ApiConnection(
            user_id=user.id,
            service="spotify",
        )
        db.add(conn)

    conn.access_token = tokens["access_token"]
    conn.refresh_token = tokens.get("refresh_token", conn.refresh_token)
    conn.token_expiry = expiry
    conn.is_connected = True
    conn.scopes = SCOPES.split()

    await db.commit()

    frontend = os.environ.get("FRONTEND_URL", "http://localhost:5173")
    return RedirectResponse(frontend + "/settings?spotify=connected")


# ---------------------------------------------------------------------------
# Token refresh helper
# ---------------------------------------------------------------------------


async def _get_valid_token(user: User, db: AsyncSession) -> str:
    """Return a valid Spotify access token, refreshing if expired."""
    result = await db.execute(
        select(ApiConnection).where(
            ApiConnection.user_id == user.id,
            ApiConnection.service == "spotify",
            ApiConnection.is_connected == True,
        )
    )
    conn = result.scalar_one_or_none()
    if conn is None:
        raise HTTPException(status_code=400, detail="Spotify not connected")

    # Refresh if expired or about to expire (60s buffer)
    if conn.token_expiry and conn.token_expiry < datetime.utcnow() + timedelta(seconds=60):
        if not conn.refresh_token:
            raise HTTPException(status_code=400, detail="Spotify refresh token missing — reconnect")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": conn.refresh_token,
                    "client_id": SPOTIFY_CLIENT_ID,
                    "client_secret": SPOTIFY_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code != 200:
                conn.is_connected = False
                await db.commit()
                raise HTTPException(status_code=400, detail="Spotify token refresh failed — reconnect")

            tokens = resp.json()
            conn.access_token = tokens["access_token"]
            if tokens.get("refresh_token"):
                conn.refresh_token = tokens["refresh_token"]
            conn.token_expiry = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
            await db.commit()

    return conn.access_token


# ---------------------------------------------------------------------------
# Data endpoints
# ---------------------------------------------------------------------------


@router.get("/spotify/recent")
async def spotify_recent(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
):
    """Return recently played tracks."""
    token = await _get_valid_token(user, db)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{API_BASE}/me/player/recently-played",
            params={"limit": limit},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Spotify API error")

        data = resp.json()

    return {
        "tracks": [
            {
                "name": item["track"]["name"],
                "artist": ", ".join(a["name"] for a in item["track"]["artists"]),
                "album": item["track"]["album"]["name"],
                "played_at": item["played_at"],
                "image": (item["track"]["album"]["images"] or [{}])[0].get("url"),
            }
            for item in data.get("items", [])
        ]
    }


@router.get("/spotify/new-releases")
async def spotify_new_releases(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return new releases from artists the user follows."""
    token = await _get_valid_token(user, db)

    async with httpx.AsyncClient() as client:
        # Get followed artists
        resp = await client.get(
            f"{API_BASE}/me/following",
            params={"type": "artist", "limit": 50},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Spotify API error")

        followed = resp.json().get("artists", {}).get("items", [])
        followed_ids = {a["id"] for a in followed}

        # Get new releases (Spotify global — we filter to followed artists)
        resp = await client.get(
            f"{API_BASE}/browse/new-releases",
            params={"limit": 50},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Spotify API error")

        albums = resp.json().get("albums", {}).get("items", [])

    # Filter to followed artists only
    relevant = []
    for album in albums:
        artist_ids = {a["id"] for a in album.get("artists", [])}
        matching = artist_ids & followed_ids
        if matching:
            relevant.append({
                "name": album["name"],
                "artist": ", ".join(a["name"] for a in album["artists"]),
                "release_date": album.get("release_date", ""),
                "type": album.get("album_type", ""),
                "image": (album.get("images") or [{}])[0].get("url"),
                "url": album.get("external_urls", {}).get("spotify"),
            })

    return {"releases": relevant, "followed_artist_count": len(followed_ids)}
