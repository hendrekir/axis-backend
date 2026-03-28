from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user
from services.morning_digest import generate_digest

router = APIRouter()


@router.get("/brief")
async def get_brief(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate and return a morning digest / brief for the user."""
    digest = await generate_digest(user, db)
    return {"brief": digest}
