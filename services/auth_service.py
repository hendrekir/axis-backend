import os

import httpx
import jwt
from jwt import PyJWKClient

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
def _get_jwks_client() -> PyJWKClient:
    jwks_url = os.getenv("CLERK_JWKS_URL", "https://tryaxis.app/.well-known/jwks.json")
    return PyJWKClient(jwks_url)


async def verify_clerk_token(token: str) -> dict | None:
    """Verify a Clerk JWT and return the claims, or None if invalid."""
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return claims
    except Exception:
        return None


async def get_clerk_user(user_id: str) -> dict | None:
    """Fetch user details from Clerk Backend API."""
    if not CLERK_SECRET_KEY:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.clerk.com/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {CLERK_SECRET_KEY}"},
        )
        if resp.status_code == 200:
            return resp.json()
    return None
