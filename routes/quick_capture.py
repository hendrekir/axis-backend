import json
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Task, Note
from routes.auth import get_authenticated_user
from services.claude_service import generate

logger = logging.getLogger("axis.capture")

router = APIRouter()

CLASSIFY_SYSTEM = """You are a smart classifier. Given user input, classify it as exactly one of: note, task, meeting, signal, idea.

Rules:
- task: actionable item the user needs to do (e.g. "call Marcus", "finish the deck")
- meeting: scheduling intent with a person and/or time (e.g. "coffee with Sarah Thursday 2pm")
- signal: something urgent or time-sensitive that needs attention now (e.g. "membrane failing on Level 2")
- idea: a concept, possibility, or creative thought (e.g. "what if we added a voice feature")
- note: everything else — observations, reminders, context

Return ONLY valid JSON:
{{"category": "task", "title": "Short title", "body": "Original content"}}
"""


class CaptureIn(BaseModel):
    content: str


@router.post("/quick-capture")
async def quick_capture(
    body: CaptureIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    raw = await generate(
        system_prompt=CLASSIFY_SYSTEM,
        user_message=body.content,
        max_tokens=256,
    )

    try:
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(cleaned)
    except Exception:
        result = {"category": "note", "title": body.content[:80], "body": body.content}

    category = result.get("category", "note")
    title = result.get("title", body.content[:80])
    original = result.get("body", body.content)

    confirmation = "Captured."

    if category == "task":
        db.add(Task(user_id=user.id, title=title, category="work", why=original))
        confirmation = "Added to your tasks."
    elif category == "meeting":
        # Return parsed intent for frontend to show ScheduleConfirmCard
        return {
            "category": "meeting",
            "needs_schedule_confirm": True,
            "parsed_intent": {"subject": title, "person": None, "datetime_str": None, "duration_minutes": 30},
            "confirmation_message": "Looks like a meeting. Confirm the details.",
        }
    elif category == "signal":
        db.add(Task(user_id=user.id, title=title, category="work", is_urgent=True, why=original))
        confirmation = "Added to your signals."
    elif category == "idea":
        db.add(Note(user_id=user.id, content=original, tags=["idea"], source="quick_capture"))
        confirmation = "Added to your ideas."
    else:
        db.add(Note(user_id=user.id, content=original, tags=[], source="quick_capture"))
        confirmation = "Added to your mind."

    await db.commit()

    return {
        "category": category,
        "needs_schedule_confirm": False,
        "confirmation_message": confirmation,
    }
