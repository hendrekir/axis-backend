"""
Weekly retrospective service — generates and sends a personal weekly summary.

Runs Sunday 6PM via APScheduler. For each Pro user:
1. Pulls week's interactions, skill executions, notes, watches
2. Calls Claude with retrospective prompt
3. Sends via Resend if API key set, otherwise saves to DB only
"""

import logging
import os
from datetime import datetime, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    AgentActivity, Interaction, Note, SkillExecution, User,
    Watch, WeeklyRetrospective,
)
from prompts.retrospective import RETROSPECTIVE_SYSTEM
from services.claude_service import generate

logger = logging.getLogger("axis.retrospective")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")


async def _build_activity_summary(user: User, week_start: datetime, db: AsyncSession) -> str:
    """Pull all activity from the past week into a text summary."""
    week_end = week_start + timedelta(days=7)
    parts = []

    # Interactions count by surface
    result = await db.execute(
        select(Interaction.surface, func.count())
        .where(
            Interaction.user_id == user.id,
            Interaction.created_at >= week_start,
            Interaction.created_at < week_end,
        )
        .group_by(Interaction.surface)
    )
    surface_counts = {row[0]: row[1] for row in result.all()}
    if surface_counts:
        parts.append("Interactions: " + ", ".join(f"{k}: {v}" for k, v in surface_counts.items()))

    # Skill executions
    result = await db.execute(
        select(SkillExecution.model_used, func.count())
        .where(
            SkillExecution.user_id == user.id,
            SkillExecution.created_at >= week_start,
            SkillExecution.created_at < week_end,
        )
        .group_by(SkillExecution.model_used)
    )
    skill_counts = {row[0] or "unknown": row[1] for row in result.all()}
    if skill_counts:
        parts.append("Skill runs: " + ", ".join(f"{k}: {v}" for k, v in skill_counts.items()))

    # Notes created
    result = await db.execute(
        select(func.count())
        .where(
            Note.user_id == user.id,
            Note.created_at >= week_start,
            Note.created_at < week_end,
        )
    )
    note_count = result.scalar() or 0
    if note_count:
        parts.append(f"Notes saved: {note_count}")

    # Agent activity highlights
    result = await db.execute(
        select(AgentActivity.skill, AgentActivity.action, AgentActivity.detail)
        .where(
            AgentActivity.user_id == user.id,
            AgentActivity.created_at >= week_start,
            AgentActivity.created_at < week_end,
        )
        .order_by(AgentActivity.created_at.desc())
        .limit(10)
    )
    activities = result.all()
    if activities:
        parts.append("Agent highlights:\n" + "\n".join(
            f"- {a.skill}/{a.action}: {(a.detail or '')[:100]}" for a in activities
        ))

    # Watch alerts
    result = await db.execute(
        select(func.count())
        .select_from(AgentActivity)
        .where(
            AgentActivity.user_id == user.id,
            AgentActivity.skill == "watch",
            AgentActivity.created_at >= week_start,
            AgentActivity.created_at < week_end,
        )
    )
    watch_alerts = result.scalar() or 0
    if watch_alerts:
        parts.append(f"Watch alerts triggered: {watch_alerts}")

    return "\n".join(parts) if parts else "Light week — not much tracked activity."


async def generate_weekly_retrospective(user: User, db: AsyncSession) -> WeeklyRetrospective:
    """Generate a retrospective for one user."""
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=7)
    week_end = today

    activity_summary = await _build_activity_summary(
        user, datetime.combine(week_start, datetime.min.time()), db
    )

    prompt = RETROSPECTIVE_SYSTEM.format(
        name=user.name or "there",
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        activity_summary=activity_summary,
    )

    content = await generate(
        system_prompt="You are Axis. Write only the retrospective email body.",
        user_message=prompt,
        max_tokens=512,
    )

    retro = WeeklyRetrospective(
        user_id=user.id,
        week_start=week_start,
        content=content.strip(),
    )
    db.add(retro)

    # Send via Resend if API key is configured
    if RESEND_API_KEY and user.gmail_connected:
        try:
            # Get user's email from Clerk (stored in gmail token context)
            await _send_email(user, content.strip(), week_start)
            retro.sent_at = datetime.utcnow()
        except Exception as e:
            logger.warning("Retrospective email send failed for %s: %s", user.name, e)

    return retro


async def _send_email(user: User, body: str, week_start) -> None:
    """Send retrospective via Resend API."""
    # We need the user's email — try to get from Gmail
    if not user.gmail_access_token:
        return

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(token=user.gmail_access_token)
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        user_email = profile.get("emailAddress")
    except Exception:
        logger.warning("Could not get email for user %s", user.id)
        return

    if not user_email:
        return

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Axis <axis@updates.dreyco.com>",
                "to": [user_email],
                "subject": f"Your week with Axis — {week_start.isoformat()}",
                "text": body,
            },
        )
        if resp.status_code not in (200, 201):
            logger.error("Resend API error: %s", resp.text)
            raise Exception(f"Resend error: {resp.status_code}")

    logger.info("Retrospective email sent to %s", user_email)


async def run_all_retrospectives(db: AsyncSession) -> list[dict]:
    """Generate retrospectives for all Pro users."""
    result = await db.execute(
        select(User).where(User.plan == "pro")
    )
    users = result.scalars().all()

    if not users:
        return []

    results = []
    for user in users:
        try:
            retro = await generate_weekly_retrospective(user, db)
            results.append({
                "user_id": str(user.id),
                "sent": retro.sent_at is not None,
            })
        except Exception as e:
            logger.error("Retrospective failed for user %s: %s", user.id, e)

    await db.commit()
    logger.info("Retrospectives complete: %d users", len(results))
    return results
