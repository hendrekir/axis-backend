import os
import logging
from jwt import PyJWKClient
import jwt

logger = logging.getLogger(__name__)

# Clerk's JWKS endpoint for your production instance
JWKS_URL = "https://clerk.tryaxis.app/.well-known/jwks.json"
_jwks_client = PyJWKClient(JWKS_URL, cache_keys=True)

async def verify_clerk_token(token: str) -> dict | None:
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return claims
    except Exception as e:
        logger.error("Token verification failed: %s", e)
        return None
