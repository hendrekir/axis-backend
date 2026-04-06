import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user
from services.claude_service import generate
from services.calendar_service import create_calendar_event

logger = logging.getLogger("axis.schedule")

router = APIRouter()


class ParseIn(BaseModel):
    message: str


class ParseOut(BaseModel):
    has_intent: bool
    person: str | None = None
    datetime_str: str | None = None
    subject: str | None = None
    duration_minutes: int = 30


class ConfirmIn(BaseModel):
    person: str | None = None
    datetime_str: str
    subject: str
    duration_minutes: int = 30


PARSE_SYSTEM = """You are a calendar intent extractor. Given a message, determine if it contains a scheduling intent.

If yes, extract:
- person: who the meeting is with (null if solo event)
- datetime_str: ISO 8601 datetime string (e.g. "2026-04-03T14:00:00")
- subject: short meeting title
- duration_minutes: estimated duration (default 30)

Today is {today}. The user's timezone is {timezone}.

Return ONLY valid JSON:
{{"has_intent": true, "person": "Marcus", "datetime_str": "2026-04-03T14:00:00", "subject": "Supplier check-in", "duration_minutes": 30}}

If no scheduling intent found:
{{"has_intent": false}}
"""


@router.post("/schedule/parse", response_model=ParseOut)
async def parse_schedule(
    body: ParseIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract calendar intent from a message using Claude."""
    import json

    prompt = PARSE_SYSTEM.format(
        today=datetime.utcnow().strftime("%Y-%m-%d"),
        timezone=user.timezone or "Australia/Brisbane",
    )

    raw = await generate(
        system_prompt=prompt,
        user_message=body.message,
        max_tokens=256,
    )

    try:
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(cleaned)
    except Exception:
        return ParseOut(has_intent=False)

    return ParseOut(**result)


@router.post("/schedule/confirm")
async def confirm_schedule(
    body: ConfirmIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Google Calendar event from a confirmed schedule parse."""
    start = datetime.fromisoformat(body.datetime_str)
    end = start + timedelta(minutes=body.duration_minutes)

    result = await create_calendar_event(
        user=user,
        db=db,
        summary=body.subject,
        start=start,
        end=end,
        attendee=body.person,
    )

    return {
        **result,
        "confirmation_message": f"Added '{body.subject}' to your calendar — {start.strftime('%A %B %d at %I:%M %p')}.",
    }
