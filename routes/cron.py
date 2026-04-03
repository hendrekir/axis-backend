import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.dispatch import run_dispatch
from services.morning_digest import run_morning_digest
from services.streak_service import run_streak_reminders

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


@router.post("/dispatch/run")
async def dispatch_manual(db: AsyncSession = Depends(get_db)):
    """Manual trigger for testing. Requires auth (not in PUBLIC_PATHS)."""
    stats = await run_dispatch(db)
    return {"status": "ok", "results": stats}
