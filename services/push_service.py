import json
import logging
import os
import time
import base64

import httpx
import jwt
from pywebpush import webpush, WebPushException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("axis.push")

APNS_KEY_ID = os.getenv("APNS_KEY_ID", "")
APNS_TEAM_ID = os.getenv("APNS_TEAM_ID", "")
APNS_CERT = os.getenv("APNS_CERT", "")  # base64-encoded .p8 key
APNS_TOPIC = "com.dreyco.axis"  # Your app bundle ID

# Use production APNs by default, sandbox for development
APNS_HOST = os.getenv("APNS_HOST", "https://api.push.apple.com")

_apns_token: str | None = None
_apns_token_time: float = 0


def _get_apns_token() -> str:
    """Generate or return cached APNs JWT (valid for 60 min, refresh at 50)."""
    global _apns_token, _apns_token_time
    now = time.time()
    if _apns_token and (now - _apns_token_time) < 3000:
        return _apns_token

    if not APNS_CERT:
        raise ValueError("APNS_CERT environment variable not set")

    key_data = base64.b64decode(APNS_CERT)
    _apns_token = jwt.encode(
        {"iss": APNS_TEAM_ID, "iat": int(now)},
        key_data,
        algorithm="ES256",
        headers={"kid": APNS_KEY_ID},
    )
    _apns_token_time = now
    return _apns_token


async def send_push(device_token: str, title: str, body: str, data: dict | None = None):
    """Send a push notification via APNs HTTP/2."""
    token = _get_apns_token()
    payload = {
        "aps": {
            "alert": {"title": title, "body": body},
            "sound": "default",
            "badge": 1,
        },
    }
    if data:
        payload["data"] = data

    async with httpx.AsyncClient(http2=True) as client:
        resp = await client.post(
            f"{APNS_HOST}/3/device/{device_token}",
            headers={
                "authorization": f"bearer {token}",
                "apns-topic": APNS_TOPIC,
                "apns-push-type": "alert",
            },
            content=json.dumps(payload),
        )
        return resp.status_code == 200


VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS = {"sub": "mailto:hello@dreyco.com.au"}


async def send_web_push(user_id, title: str, body: str, url: str = "/situation", db: AsyncSession = None):
    """Send web push notification to all subscriptions for a user."""
    if not VAPID_PRIVATE_KEY or not db:
        return

    from models import PushSubscription

    result = await db.execute(
        select(PushSubscription).where(PushSubscription.user_id == user_id)
    )
    subscriptions = result.scalars().all()

    payload = json.dumps({"title": title, "body": body, "url": url})

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={"endpoint": sub.endpoint, "keys": sub.keys},
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
        except WebPushException as e:
            logger.warning("Web push failed for %s: %s", sub.endpoint[:50], e)
            if "410" in str(e) or "404" in str(e):
                await db.delete(sub)
                await db.commit()
