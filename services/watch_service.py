"""
Watch service — monitors topics and alerts on material changes.

Watches run hourly via APScheduler. Each watch:
1. Checks for new information (Perplexity for web, Gmail for people)
2. Compares to last_result
3. Surfaces to thread if material change detected
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Watch, ThreadMessage, AgentActivity
from services.claude_service import generate
from services.model_router import route
from services.push_service import send_push

logger = logging.getLogger("axis.watch")


async def create_watch(
    user_id,
    topic: str,
    watch_type: str = "general",
    db: AsyncSession = None,
) -> Watch:
    """Create a new watch and run an immediate first check."""
    watch = Watch(
        user_id=user_id,
        topic=topic,
        watch_type=watch_type,
    )
    db.add(watch)
    await db.flush()

    # Run immediate first check to establish baseline
    first_result = await _fetch_current(topic, watch_type)
    watch.last_result = first_result
    watch.last_checked_at = datetime.utcnow()

    logger.info("Watch created for user %s: '%s' (type: %s)", user_id, topic, watch_type)
    return watch


async def _fetch_current(topic: str, watch_type: str) -> str:
    """Fetch current state of a topic via the appropriate model."""
    if watch_type in ("news", "general", "web"):
        try:
            result = await route(
                task_type="current_events",
                system="You are a concise research assistant. Summarise the current state of the topic in 2-3 sentences. Focus on the most recent developments. Include dates.",
                user_msg=f"Current status of: {topic}",
                max_tokens=256,
            )
            return result["text"]
        except Exception as e:
            logger.warning("Perplexity watch fetch failed, falling back to Claude: %s", e)

    # Fallback to Claude
    return await generate(
        system_prompt="Summarise what you know about this topic in 2-3 sentences. Be specific and date-aware.",
        user_message=f"Current status of: {topic}",
        max_tokens=256,
    )


async def check_watch(watch: Watch, user: User, db: AsyncSession) -> str | None:
    """Check a single watch. Returns alert text if material change detected, else None."""
    current = await _fetch_current(watch.topic, watch.watch_type)

    # Compare with last result
    if not watch.last_result:
        watch.last_result = current
        watch.last_checked_at = datetime.utcnow()
        return None

    # Ask Claude to compare
    comparison = await generate(
        system_prompt="You compare two snapshots of a topic. Reply with ONLY 'CHANGED: <one sentence summary>' if there is a material change, or 'NO_CHANGE' if nothing significant changed.",
        user_message=f"Topic: {watch.topic}\n\nPrevious:\n{watch.last_result}\n\nCurrent:\n{current}",
        max_tokens=128,
    )

    watch.last_result = current
    watch.last_checked_at = datetime.utcnow()

    if comparison.strip().startswith("CHANGED:"):
        change_summary = comparison.strip().replace("CHANGED:", "").strip()
        return change_summary

    return None


async def run_all_watches(db: AsyncSession) -> list[dict]:
    """Check all active watches. Called hourly by APScheduler."""
    result = await db.execute(
        select(Watch, User)
        .join(User, Watch.user_id == User.id)
        .where(Watch.is_active == True)
    )
    rows = result.all()

    if not rows:
        return []

    alerts = []
    for watch, user in rows:
        try:
            change = await check_watch(watch, user, db)
            if change:
                # Surface to thread
                msg = ThreadMessage(
                    user_id=user.id,
                    role="assistant",
                    content=f"**Watch alert: {watch.topic}**\n{change}",
                    message_type="intel",
                    source_skill="watch",
                )
                db.add(msg)

                # Push notification
                if user.apns_token:
                    await send_push(
                        user.apns_token,
                        f"Watch: {watch.topic[:40]}",
                        change[:100],
                        data={"action_type": "watch_alert", "watch_id": str(watch.id)},
                    )

                # Log activity
                db.add(AgentActivity(
                    user_id=user.id,
                    skill="watch",
                    action="alert_triggered",
                    detail=f"Topic: {watch.topic}",
                    result=change[:500],
                ))

                alerts.append({
                    "user_id": str(user.id),
                    "topic": watch.topic,
                    "change": change,
                })
        except Exception as e:
            logger.error("Watch check failed for '%s' (user %s): %s", watch.topic, user.id, e)

    await db.commit()
    logger.info("Watch cycle complete: %d watches checked, %d alerts", len(rows), len(alerts))
    return alerts
