import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from database import get_db
from models import User
from services.dispatch import run_dispatch
from services.morning_digest import run_morning_digest
from services.streak_service import run_streak_reminders
from services.push_service import send_web_push

router = APIRouter(tags=["Cron"])

CRON_SECRET = os.getenv("CRON_SECRET", "")


def _verify_cron_secret(secret: str):
    """Verify the cron request is authentic."""
    if not CRON_SECRET:
        return  # No secret configured — allow (dev mode)
    if secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")


@router.post("/cron/dispatch")
async def dispatch_cron(secret: str = "", db: AsyncSession = Depends(get_db)):
    """15-minute dispatch job. Called by Railway cron."""
    _verify_cron_secret(secret)
    stats = await run_dispatch(db)
    return {"status": "ok", "results": stats}


@router.post("/cron/digest")
async def digest_cron(secret: str = "", db: AsyncSession = Depends(get_db)):
    """Morning digest job. Called by Railway cron every 15 min, fires at 6:50AM user local time."""
    _verify_cron_secret(secret)
    results = await run_morning_digest(db)
    return {"status": "ok", "results": results}


@router.post("/cron/streak-reminder")
async def streak_reminder_cron(secret: str = "", db: AsyncSession = Depends(get_db)):
    """Daily 9AM AEST re-engagement push. Called by Railway cron."""
    _verify_cron_secret(secret)
    count = await run_streak_reminders(db)
    return {"status": "ok", "users_reminded": count}


JOURNAL_QUESTIONS = {
    0: "What's the one thing that would make this week a win?",
    1: "What are you avoiding right now, and why?",
    2: "Who do you need to reach out to that you've been putting off?",
    3: "What decision are you sitting on that needs to be made?",
    4: "What's one thing you learned or noticed this week?",
    5: "What drained you this week? What energised you?",
    6: "What do you want to be different next week?",
}


@router.post("/cron/journal-prompt")
async def journal_prompt_cron(secret: str = "", db: AsyncSession = Depends(get_db)):
    """Daily 8PM AEST journal push. Called by Railway cron."""
    _verify_cron_secret(secret)
    from datetime import date
    question = JOURNAL_QUESTIONS.get(date.today().weekday(), "What's on your mind?")

    result = await db.execute(select(User))
    users = result.scalars().all()
    count = 0
    for user in users:
        await send_web_push(user.id, "Axis", f"One question for today: {question}", url="/mind", db=db)
        count += 1

    return {"status": "ok", "users_prompted": count, "question": question}


@router.post("/dispatch/run")
async def dispatch_manual(db: AsyncSession = Depends(get_db)):
    """Manual trigger for testing. Requires auth (not in PUBLIC_PATHS)."""
    stats = await run_dispatch(db)
    return {"status": "ok", "results": stats}
