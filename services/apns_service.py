"""APNs notification service.

Sends categorised push notifications via Apple's HTTP/2 APNs API using a
.p8 key + ES256 JWT. Categories match the iOS notification category
identifiers used by the lock-screen action buttons.
"""
import base64
import json
import logging
import os
import time

import httpx
import jwt

logger = logging.getLogger("axis.apns")

APNS_KEY_ID = os.getenv("APNS_KEY_ID", "")
APNS_TEAM_ID = os.getenv("APNS_TEAM_ID", "")
APNS_BUNDLE_ID = os.getenv("APNS_BUNDLE_ID", "com.dreyco.axis")
# Either APNS_PRIVATE_KEY (raw .p8 contents) or APNS_CERT (base64-encoded .p8)
APNS_PRIVATE_KEY = os.getenv("APNS_PRIVATE_KEY", "") or os.getenv("APNS_CERT", "")

APNS_HOST = os.getenv("APNS_HOST", "https://api.push.apple.com")

# Categories — must match iOS UNNotificationCategory identifiers
CAT_DEPARTURE_ALERT = "DEPARTURE_ALERT"
CAT_NOW_SIGNAL = "NOW_SIGNAL"
CAT_MEETING_PREP = "MEETING_PREP"
CAT_SILENCE_DETECTED = "SILENCE_DETECTED"
CAT_EMAIL_DRAFT = "EMAIL_DRAFT"
CAT_MORNING_BRIEF = "MORNING_BRIEF"

_jwt_token: str | None = None
_jwt_token_time: float = 0


def _load_key() -> bytes:
    if not APNS_PRIVATE_KEY:
        raise ValueError("APNS_PRIVATE_KEY (or APNS_CERT) not set")
    raw = APNS_PRIVATE_KEY.strip()
    if raw.startswith("-----BEGIN"):
        return raw.encode("utf-8")
    # Assume base64-encoded .p8
    try:
        return base64.b64decode(raw)
    except Exception:
        return raw.encode("utf-8")


def _get_jwt() -> str:
    """Generate or return cached APNs JWT (valid 60min, refresh at 50min)."""
    global _jwt_token, _jwt_token_time
    now = time.time()
    if _jwt_token and (now - _jwt_token_time) < 3000:
        return _jwt_token

    key = _load_key()
    _jwt_token = jwt.encode(
        {"iss": APNS_TEAM_ID, "iat": int(now)},
        key,
        algorithm="ES256",
        headers={"kid": APNS_KEY_ID},
    )
    _jwt_token_time = now
    return _jwt_token


async def send_notification(
    device_token: str,
    title: str,
    body: str,
    category: str,
    data: dict | None = None,
    badge: int = 1,
) -> bool:
    """Low-level: send a single push to one device token."""
    if not device_token:
        return False
    if not APNS_PRIVATE_KEY or not APNS_KEY_ID or not APNS_TEAM_ID:
        logger.warning("APNs not configured — skipping push to %s", device_token[:8])
        return False

    try:
        token = _get_jwt()
    except Exception as e:
        logger.error("APNs JWT generation failed: %s", e)
        return False

    payload: dict = {
        "aps": {
            "alert": {"title": title, "body": body},
            "sound": "default",
            "badge": badge,
            "category": category,
            "mutable-content": 1,
        },
    }
    if data:
        payload["data"] = data

    try:
        async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
            resp = await client.post(
                f"{APNS_HOST}/3/device/{device_token}",
                headers={
                    "authorization": f"bearer {token}",
                    "apns-topic": APNS_BUNDLE_ID,
                    "apns-push-type": "alert",
                    "apns-priority": "10",
                },
                content=json.dumps(payload),
            )
            if resp.status_code == 200:
                return True
            logger.warning(
                "APNs send failed (%s): %s", resp.status_code, resp.text[:200]
            )
            return False
    except Exception as e:
        logger.error("APNs send exception: %s", e)
        return False


# ---- High-level category helpers ------------------------------------------------


async def send_departure_alert(user, event_title: str, minutes_until: int, drive_time: int) -> bool:
    title = f"Leave in {minutes_until} min"
    body = f"{event_title} — {drive_time} min drive"
    return await send_notification(
        user.apns_token,
        title,
        body,
        CAT_DEPARTURE_ALERT,
        data={
            "type": "departure_alert",
            "event_title": event_title,
            "minutes_until": minutes_until,
            "drive_time": drive_time,
        },
    )


async def send_now_signal(user, signal: dict) -> bool:
    title = (signal.get("title") or signal.get("summary") or "New signal")[:60]
    body = (signal.get("pre_prepared_action") or signal.get("body") or "")[:120]
    return await send_notification(
        user.apns_token,
        title,
        body,
        CAT_NOW_SIGNAL,
        data={
            "type": "now_signal",
            "signal_id": str(signal.get("id") or signal.get("item_id") or ""),
            "action_type": signal.get("action_type", "none"),
            "skill": signal.get("skill_name", ""),
        },
    )


async def send_meeting_prep(user, event: dict) -> bool:
    event_id = str(event.get("id", ""))
    title = f"Meeting soon — {event.get('title', 'Untitled')}"
    body = (event.get("brief") or event.get("summary") or "Tap for brief")[:120]
    return await send_notification(
        user.apns_token,
        title,
        body,
        CAT_MEETING_PREP,
        data={
            "type": "meeting_prep",
            "event_id": event_id,
            "starts_at": str(event.get("start_dt", "")),
            "deep_link": event.get("deep_link", f"axis://meeting/{event_id}"),
        },
    )


async def send_silence_detected(user, person: str, days_silent: int) -> bool:
    title = f"You haven't spoken to {person}"
    body = f"{days_silent} days of silence"
    return await send_notification(
        user.apns_token,
        title,
        body,
        CAT_SILENCE_DETECTED,
        data={
            "type": "silence_detected",
            "person": person,
            "days_silent": days_silent,
        },
    )


async def send_email_draft(user, draft_preview: str, signal_id) -> bool:
    title = "Draft ready to send"
    body = draft_preview[:150]
    return await send_notification(
        user.apns_token,
        title,
        body,
        CAT_EMAIL_DRAFT,
        data={
            "type": "email_draft",
            "signal_id": str(signal_id),
        },
    )


async def send_morning_brief(user, summary: str) -> bool:
    title = "Morning brief"
    body = summary[:200]
    return await send_notification(
        user.apns_token,
        title,
        body,
        CAT_MORNING_BRIEF,
        data={"type": "morning_brief"},
    )


# ---- Dispatch routing -----------------------------------------------------------

async def send_for_signal(user, item: dict) -> bool:
    """Route a dispatch item to the correct categorised APNs helper."""
    if not getattr(user, "apns_token", None):
        return False

    action_type = (item.get("action_type") or "").lower()
    skill = (item.get("skill_name") or "").lower()

    if action_type == "departure_alert" or skill == "travel_time":
        return await send_departure_alert(
            user,
            event_title=item.get("event_title") or item.get("title", ""),
            minutes_until=int(item.get("minutes_until", 0) or 0),
            drive_time=int(item.get("drive_time", 0) or 0),
        )
    if action_type == "meeting_prep" or skill == "meeting_prep":
        return await send_meeting_prep(user, item)
    if action_type == "silence_detected" or skill == "silence":
        return await send_silence_detected(
            user,
            person=item.get("person", "them"),
            days_silent=int(item.get("days_silent", 0) or 0),
        )
    if action_type in ("send_reply", "email_draft") or skill == "email_draft":
        return await send_email_draft(
            user,
            draft_preview=item.get("pre_prepared_action") or item.get("draft_preview", ""),
            signal_id=item.get("item_id") or item.get("id", ""),
        )
    if action_type == "morning_brief" or skill == "morning_brief":
        return await send_morning_brief(user, item.get("summary", ""))

    return await send_now_signal(user, item)
