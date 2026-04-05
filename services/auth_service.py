import os
import logging

from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions

logger = logging.getLogger(__name__)

_clerk_client = None


def _get_clerk() -> Clerk:
    global _clerk_client
    if _clerk_client is None:
        secret_key = os.environ.get("CLERK_SECRET_KEY")
        if not secret_key:
            raise RuntimeError("CLERK_SECRET_KEY not set")
        _clerk_client = Clerk(bearer_auth=secret_key)
    return _clerk_client


class _TokenRequest:
    """Minimal request object satisfying Clerk's Requestish protocol."""
    def __init__(self, token: str):
        self.headers = {"Authorization": f"Bearer {token}"}


async def verify_clerk_token(token: str) -> dict | None:
    """Verify a Clerk JWT and return the claims, or None if invalid."""
    try:
        client = _get_clerk()
        req = _TokenRequest(token)
        state = client.authenticate_request(
            req,
            AuthenticateRequestOptions(
                secret_key=os.environ.get("CLERK_SECRET_KEY"),
            ),
        )
        if not state.is_signed_in:
            logger.warning("Token not signed in: %s", state.reason or state.message)
            return None
        return state.payload
    except Exception as e:
        logger.error("Token verification failed: %s", e)
        return None
