from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from services.auth_service import verify_clerk_token


async def get_current_user(token: str, db: AsyncSession | None = None) -> User | None:
    """Verify a Clerk JWT and return the matching User from the database.

    When called from middleware (no db session), returns a lightweight
    user dict with clerk_id. Routes that need the full User object
    should use get_authenticated_user dependency instead.
    """
    claims = await verify_clerk_token(token)
    if claims is None:
        return None

    clerk_id = claims.get("sub")
    if not clerk_id:
        return None

    if db is None:
        # Middleware call — return minimal user info as a dict-like object
        # The full DB lookup happens in get_authenticated_user
        class MinimalUser:
            def __init__(self, clerk_id):
                self.clerk_id = clerk_id
        return MinimalUser(clerk_id)

    # Full DB lookup
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    return result.scalar_one_or_none()


async def get_authenticated_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """FastAPI dependency — returns the full User model or 401s."""
    minimal_user = getattr(request.state, "user", None)
    if minimal_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    result = await db.execute(select(User).where(User.clerk_id == minimal_user.clerk_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(clerk_id=minimal_user.clerk_id, mode="personal", plan="free")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
