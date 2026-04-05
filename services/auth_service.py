import os
import logging

from clerk_backend_api.jwks_helpers import verify_token as clerk_verify_token, VerifyTokenOptions

logger = logging.getLogger(__name__)


async def verify_clerk_token(token: str) -> dict | None:
    """Verify a Clerk JWT and return the claims, or None if invalid."""
    try:
        claims = clerk_verify_token(
            token,
            VerifyTokenOptions(secret_key=os.environ.get("CLERK_SECRET_KEY")),
        )
        return claims
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None
