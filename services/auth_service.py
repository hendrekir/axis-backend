import os
import logging

from clerk_backend_api import Clerk

logger = logging.getLogger(__name__)

_clerk_client = None


def get_clerk_client():
    global _clerk_client
    if _clerk_client is None:
        secret_key = os.environ.get("CLERK_SECRET_KEY")
        if not secret_key:
            raise RuntimeError("CLERK_SECRET_KEY not set")
        _clerk_client = Clerk(bearer_auth=secret_key)
    return _clerk_client


async def verify_clerk_token(token: str) -> dict | None:
    """Verify a Clerk JWT and return the claims, or None if invalid."""
    try:
        client = get_clerk_client()
        claims = client.verify_token(token)
        return claims
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None
