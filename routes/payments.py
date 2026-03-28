import hashlib
import hmac
import os

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from database import async_session
from models import User

router = APIRouter()

REVENUECAT_WEBHOOK_SECRET = os.getenv("REVENUECAT_WEBHOOK_SECRET", "")


@router.post("/revenuecat")
async def revenuecat_webhook(request: Request):
    """Handle RevenueCat subscription webhooks.

    Events: INITIAL_PURCHASE, RENEWAL, CANCELLATION, EXPIRATION, etc.
    """
    # Verify webhook signature if secret is configured
    if REVENUECAT_WEBHOOK_SECRET:
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {REVENUECAT_WEBHOOK_SECRET}":
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

    body = await request.json()
    event = body.get("event", {})
    event_type = event.get("type", "")
    app_user_id = event.get("app_user_id", "")

    if not app_user_id:
        return {"status": "ignored", "reason": "no app_user_id"}

    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.clerk_id == app_user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return {"status": "ignored", "reason": "user not found"}

        if event_type in ("INITIAL_PURCHASE", "RENEWAL", "PRODUCT_CHANGE"):
            # Determine plan from product ID
            product_id = event.get("product_id", "")
            if "team" in product_id.lower():
                user.plan = "team"
            else:
                user.plan = "pro"
            expiration = event.get("expiration_at_ms")
            if expiration:
                from datetime import datetime
                user.plan_expires = datetime.fromtimestamp(expiration / 1000)

        elif event_type in ("CANCELLATION", "EXPIRATION"):
            user.plan = "free"
            user.plan_expires = None

        await db.commit()

    return {"status": "processed", "event_type": event_type, "user": app_user_id}
