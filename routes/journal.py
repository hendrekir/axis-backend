import json
import logging
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, JournalEntry
from routes.auth import get_authenticated_user
from services.claude_service import generate
from services.streak_service import touch_streak

logger = logging.getLogger("axis.journal")

router = APIRouter()

EXTRACT_SYSTEM = """Extract key context from this journal entry to improve Axis's understanding of this user.

Entry question: {question}
Entry answer: {answer}

Return ONLY valid JSON:
{{
  "people_mentioned": [],
  "projects_mentioned": [],
  "emotions": [],
  "decisions": [],
  "blockers": [],
  "context_summary": "one sentence summary to append to user context"
}}"""


class JournalIn(BaseModel):
    question: str
    answer: str


@router.post("/journal")
async def create_journal_entry(
    body: JournalIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()

    entry = JournalEntry(
        user_id=user.id,
        question=body.question,
        answer=body.answer,
        date=today,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    # Touch streak on journal entry
    await touch_streak(user.id, db)

    # Extract context async (best-effort)
    try:
        raw = await generate(
            system_prompt=EXTRACT_SYSTEM.format(question=body.question, answer=body.answer),
            user_message=body.answer,
            max_tokens=512,
        )
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        extracted = json.loads(cleaned)

        entry.extracted_people = extracted.get("people_mentioned", [])
        entry.extracted_projects = extracted.get("projects_mentioned", [])
        entry.extracted_emotions = extracted.get("emotions", [])
        entry.extracted_context = extracted.get("context_summary", "")

        # Append context summary to user's context_notes
        summary = extracted.get("context_summary", "")
        if summary:
            existing = user.context_notes or ""
            user.context_notes = (existing + "\n" + summary).strip() if existing else summary

        await db.commit()
    except Exception as e:
        logger.warning("Journal context extraction failed: %s", e)

    return {
        "id": str(entry.id),
        "date": str(today),
        "message": "Axis is learning from this.",
    }


@router.get("/journal")
async def get_journal_entries(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(30)
    )
    entries = result.scalars().all()

    return {
        "entries": [
            {
                "id": str(e.id),
                "question": e.question,
                "answer": e.answer,
                "date": str(e.date),
                "extracted_context": e.extracted_context,
            }
            for e in entries
        ]
    }
