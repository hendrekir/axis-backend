import os

import httpx
import jwt
from jwt import PyJWKClient

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "https://primary-polliwog-70.clerk.accounts.dev/.well-known/jwks.json")

# Cache the JWKS client — it fetches keys on first use and caches them
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        # Derive JWKS URL from Clerk frontend API if not set explicitly
        jwks_url = CLERK_JWKS_URL
        if not jwks_url:
            # Clerk publishable key format: pk_test_<base64>.clerk.accounts.dev
            # JWKS is at https://<frontend-api>/.well-known/jwks.json
            pk = os.getenv("CLERK_PUBLISHABLE_KEY", "")
            if pk:
                # Extract the domain from publishable key
                parts = pk.replace("pk_test_", "").replace("pk_live_", "")
                jwks_url = f"https://{parts}/.well-known/jwks.json"
            else:
                raise ValueError("CLERK_JWKS_URL or CLERK_PUBLISHABLE_KEY must be set")
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


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
