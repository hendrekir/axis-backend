"""
Apprentice dashboard routes — surfaces what Axis has learned about the user.

GET  /apprentice          — plain-English insights derived from user_model
PATCH /apprentice/correct — user flags an incorrect pattern
"""

import json
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Interaction, User, UserModel
from routes.auth import get_authenticated_user
from services.claude_service import generate

logger = logging.getLogger("axis.apprentice")

router = APIRouter(tags=["Apprentice"])

INSIGHTS_SYSTEM = """You are Axis summarising what you've learned about {name}.
Convert the raw JSON data into plain-English insights a normal person would understand.
Be specific, warm, and direct. No jargon. No filler.

Return ONLY valid JSON with this exact structure (no markdown fences):
{{
  "voice_insights": ["insight 1", "insight 2"],
  "time_patterns": ["insight 1", "insight 2"],
  "relationship_insights": ["insight 1", "insight 2"],
  "attention_patterns": ["insight 1", "insight 2"],
  "learned_this_week": "One sentence summary of the most interesting thing learned recently."
}}

Rules:
- Each insight is one short sentence (under 20 words)
- Be concrete: "You reply to Marcus within 2 hours" not "You respond quickly to important contacts"
- If a section has no data, return an empty array for that key
- 2-4 insights per section max
- Never invent data — only describe what the JSON actually contains
"""


@router.get("/apprentice")
async def get_apprentice(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Return plain-English insights from the user model."""
    result = await db.execute(
        select(UserModel).where(UserModel.user_id == user.id)
    )
    model = result.scalar_one_or_none()

    # Empty or missing user model — still learning
    if model is None or _is_empty(model):
        return {
            "status": "learning",
            "message": "Axis is still learning your patterns. Check back after a few days of use.",
        }

    # Build raw data summary for Claude
    raw_data = {
        "voice_patterns": model.voice_patterns or {},
        "relationship_graph": model.relationship_graph or {},
        "productive_windows": model.productive_windows or {},
        "completion_rates": model.completion_rates or {},
        "notif_response_rates": model.notif_response_rates or {},
        "defer_patterns": model.defer_patterns or {},
    }

    prompt = INSIGHTS_SYSTEM.format(name=user.name or "there")
    user_msg = f"Raw user model data:\n{json.dumps(raw_data, indent=2, default=str)}"

    raw = await generate(
        system_prompt=prompt,
        user_message=user_msg,
        max_tokens=1024,
    )

    # Parse Claude's response
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    try:
        insights = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("Claude returned invalid JSON for apprentice insights: %s", raw[:300])
        insights = {
            "voice_insights": [],
            "time_patterns": [],
            "relationship_insights": [],
            "attention_patterns": [],
            "learned_this_week": "Axis is processing your patterns.",
        }

    return {
        "status": "ready",
        "insights": insights,
        "last_updated": model.updated_at.isoformat() if model.updated_at else None,
    }


class CorrectionRequest(BaseModel):
    pattern_type: str
    correction: str


@router.patch("/apprentice/correct")
async def correct_apprentice(
    body: CorrectionRequest,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Log a user correction to a learned pattern."""
    valid_types = {
        "voice_insights", "time_patterns",
        "relationship_insights", "attention_patterns",
    }
    if body.pattern_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"pattern_type must be one of: {', '.join(sorted(valid_types))}",
        )

    db.add(Interaction(
        user_id=user.id,
        surface="apprentice",
        content_type=body.pattern_type,
        content_id=None,
        action_taken="correction",
        mode=user.mode,
    ))
    await db.commit()

    logger.info(
        "Apprentice correction from %s: %s — %s",
        user.name, body.pattern_type, body.correction[:100],
    )

    return {"status": "logged", "pattern_type": body.pattern_type}


def _is_empty(model: UserModel) -> bool:
    """Check if a user model has any meaningful data."""
    return all(
        not getattr(model, field, None)
        for field in (
            "voice_patterns", "relationship_graph", "productive_windows",
            "completion_rates", "notif_response_rates", "defer_patterns",
        )
    )
