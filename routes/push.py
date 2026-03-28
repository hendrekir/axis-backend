from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user

router = APIRouter()


class RegisterTokenIn(BaseModel):
    apns_token: str


@router.post("/push/register")
async def register_push_token(
    body: RegisterTokenIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Register or update an APNs device token for push notifications."""
    user.apns_token = body.apns_token
    await db.commit()
    return {"status": "registered"}
