from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user

router = APIRouter(tags=["User"])


@router.get("/me")
async def get_me(user: User = Depends(get_authenticated_user)):
    """Return the current user's profile."""
    return {
        "id": str(user.id),
        "name": user.name,
        "mode": user.mode,
        "timezone": user.timezone,
        "plan": user.plan,
        "gmail_connected": user.gmail_connected,
    }
