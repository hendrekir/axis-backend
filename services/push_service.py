import json
import os
import time
import base64

import httpx
import jwt

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
