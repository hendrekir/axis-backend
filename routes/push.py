from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, PushSubscription
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


class WebPushSubscribeIn(BaseModel):
    endpoint: str
    keys: dict


@router.post("/push/subscribe")
async def subscribe_web_push(
    body: WebPushSubscribeIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a web push subscription (VAPID)."""
    # Upsert — update keys if endpoint already exists
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user.id,
            PushSubscription.endpoint == body.endpoint,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.keys = body.keys
    else:
        db.add(PushSubscription(
            user_id=user.id,
            endpoint=body.endpoint,
            keys=body.keys,
        ))

    await db.commit()
    return {"status": "subscribed"}
