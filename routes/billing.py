import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models import User
from routes.auth import get_authenticated_user

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")


@router.post("/billing/checkout")
async def create_checkout(user: User = Depends(get_authenticated_user)):
    """Create a Stripe Checkout session for the $9/mo Pro plan."""
    if not STRIPE_PRICE_ID:
        raise HTTPException(status_code=500, detail="Stripe price not configured")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url="https://axis-web-chi.vercel.app/settings?upgraded=true",
        cancel_url="https://axis-web-chi.vercel.app/brain-dump",
        client_reference_id=user.clerk_id,
    )
    return {"url": session.url}


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events — upgrade user on successful checkout."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
    else:
        import json
        event = json.loads(payload)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        clerk_id = session.get("client_reference_id")
        if not clerk_id:
            return {"status": "ignored", "reason": "no client_reference_id"}

        async with async_session() as db:
            result = await db.execute(select(User).where(User.clerk_id == clerk_id))
            user = result.scalar_one_or_none()
            if user:
                user.plan = "pro"
                await db.commit()
                return {"status": "upgraded", "user": clerk_id}
            return {"status": "ignored", "reason": "user not found"}

    return {"status": "ignored", "event": event["type"]}
