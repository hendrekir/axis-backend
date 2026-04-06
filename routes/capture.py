import json
import logging
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Task
from routes.auth import get_authenticated_user
from services.claude_service import generate
from services.streak_service import touch_streak

logger = logging.getLogger("axis.capture")

router = APIRouter(prefix="/capture", tags=["Capture"])

CAPTURE_CLASSIFY_SYSTEM = """Classify this capture into exactly one of:
- relationship_task (involves a person)
- calendar_task (needs scheduling)
- research_task (find information or product)
- reminder (time or location based)
- discovery_intent (want to learn about something)
- follow_up (something promised to someone)
- personal_goal (habit, aspiration, improvement)

Extract:
- person (if any, otherwise null)
- urgency (1-10)
- suggested_surface_time: "morning" | "quiet_gap" | "contextual" | "weekly"

Return ONLY valid JSON:
{"capture_type": "...", "title": "short title", "person": null, "urgency": 5, "suggested_surface_time": "morning"}
"""


class CaptureIn(BaseModel):
    content: str


@router.post("")
async def create_capture(
    body: CaptureIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Save immediately as a capture task
    task = Task(
        user_id=user.id,
        title=body.content[:200],
        category="capture",
        is_urgent=False,
    )
    db.add(task)
    await db.flush()  # get task.id

    # 2. Classify via Claude
    capture_type = "reminder"
    person = None
    urgency = 5
    suggested_time = "morning"
    title = body.content[:200]

    try:
        raw = await generate(
            system_prompt=CAPTURE_CLASSIFY_SYSTEM,
            user_message=body.content,
            max_tokens=256,
        )
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip())
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        result = json.loads(cleaned)

        capture_type = result.get("capture_type", "reminder")
        person = result.get("person")
        urgency = result.get("urgency", 5)
        suggested_time = result.get("suggested_surface_time", "morning")
        if result.get("title"):
            title = result["title"]
    except Exception as e:
        logger.warning("Capture classification failed for user %s: %s", user.id, e)

    # 3. Update the task with classification
    task.title = title
    task.category = capture_type
    task.is_urgent = urgency >= 8

    await touch_streak(user, db)
    await db.commit()

    return {
        "id": str(task.id),
        "content": body.content,
        "capture_type": capture_type,
        "person": person,
        "urgency": urgency,
        "suggested_time": suggested_time,
    }


@router.get("")
async def list_captures(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return recent unhandled captures (not done, category still from capture classifier)."""
    capture_categories = [
        "capture", "relationship_task", "calendar_task", "research_task",
        "reminder", "discovery_intent", "follow_up", "personal_goal",
    ]
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == user.id,
            Task.is_done == False,
            Task.category.in_(capture_categories),
        )
        .order_by(Task.created_at.desc())
        .limit(50)
    )
    tasks = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "content": t.title,
            "capture_type": t.category,
            "is_urgent": t.is_urgent,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]
