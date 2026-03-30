"""
Apprentice — weekly improvement cycle and voice model rebuild.

Sunday 3AM UTC: analyse 7 days of interactions, update user_model
Sunday 4AM UTC: rebuild voice_patterns from sent_emails_cache
"""

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, UserModel, Interaction, SentEmailsCache
from services.claude_service import generate

logger = logging.getLogger("axis.apprentice")

IMPROVEMENT_SYSTEM = """You are analysing one week of user interaction data for Axis.
Your job: update the user model based on observed patterns.

Return JSON with these keys (preserve existing values where no new signal):
{
  "productive_windows": {"best_hours": [...], "interests": [...]},
  "completion_rates": {"work": 0.0-1.0, "health": 0.0-1.0, ...},
  "notif_response_rates": {"push": 0.0-1.0, "digest": 0.0-1.0},
  "defer_patterns": {"categories_deferred": [...], "avg_defer_hours": ...}
}

Only update fields where you have clear signal. Return valid JSON only.
"""

VOICE_MODEL_SYSTEM = """Analyse these sent emails to extract the user's writing patterns.

Return JSON:
{
  "avg_word_count": number,
  "formality_by_type": {"client": "formal", "colleague": "casual", ...},
  "common_sign_offs": ["Cheers", ...],
  "common_openers": ["Hi", ...],
  "sentence_style": "short and direct" | "detailed and thorough" | ...,
  "tone": "warm" | "professional" | "casual" | ...
}

Only report patterns you observe. Return valid JSON only.
"""


async def run_improvement_cycle(user: User, db: AsyncSession) -> dict:
    """Analyse last 7 days of interactions, update user_model."""
    cutoff = datetime.utcnow() - timedelta(days=7)

    # Pull interaction summary
    result = await db.execute(
        select(
            Interaction.surface,
            Interaction.content_type,
            Interaction.action_taken,
            func.count().label("count"),
        )
        .where(Interaction.user_id == user.id, Interaction.created_at >= cutoff)
        .group_by(Interaction.surface, Interaction.content_type, Interaction.action_taken)
    )
    rows = result.all()

    if not rows:
        logger.info("No interactions for user %s in last 7 days — skipping", user.id)
        return {"status": "skipped", "reason": "no interactions"}

    summary = "\n".join(
        f"surface={r[0]} content_type={r[1]} action={r[2]} count={r[3]}"
        for r in rows
    )

    # Load existing user model
    result = await db.execute(select(UserModel).where(UserModel.user_id == user.id))
    user_model = result.scalar_one_or_none()
    if not user_model:
        user_model = UserModel(user_id=user.id)
        db.add(user_model)

    existing = json.dumps({
        "productive_windows": user_model.productive_windows or {},
        "completion_rates": user_model.completion_rates or {},
        "notif_response_rates": user_model.notif_response_rates or {},
        "defer_patterns": user_model.defer_patterns or {},
    })

    prompt = f"Existing user model:\n{existing}\n\nLast 7 days interactions:\n{summary}"

    raw = await generate(system_prompt=IMPROVEMENT_SYSTEM, user_message=prompt, max_tokens=1024)

    # Parse and update
    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        updates = json.loads(cleaned)

        if "productive_windows" in updates:
            user_model.productive_windows = updates["productive_windows"]
        if "completion_rates" in updates:
            user_model.completion_rates = updates["completion_rates"]
        if "notif_response_rates" in updates:
            user_model.notif_response_rates = updates["notif_response_rates"]
        if "defer_patterns" in updates:
            user_model.defer_patterns = updates["defer_patterns"]

        await db.commit()
        logger.info("Improvement cycle complete for user %s", user.id)
        return {"status": "updated", "fields": list(updates.keys())}

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse improvement response for user %s: %s", user.id, e)
        return {"status": "error", "reason": str(e)}


async def rebuild_voice_model(user: User, db: AsyncSession) -> dict:
    """Rebuild voice_patterns from sent_emails_cache."""
    result = await db.execute(
        select(SentEmailsCache)
        .where(SentEmailsCache.user_id == user.id)
        .order_by(SentEmailsCache.sent_at.desc())
        .limit(50)
    )
    emails = result.scalars().all()

    if not emails:
        logger.info("No sent emails for user %s — skipping voice rebuild", user.id)
        return {"status": "skipped", "reason": "no sent emails"}

    emails_text = "\n\n".join(
        f"To: {e.recipient} ({e.recipient_type or 'unknown'})\n"
        f"Subject: {e.subject}\n"
        f"Summary: {e.body_summary}\n"
        f"Words: {e.word_count}"
        for e in emails
    )

    raw = await generate(
        system_prompt=VOICE_MODEL_SYSTEM,
        user_message=f"Sent emails from {user.name or 'user'}:\n\n{emails_text}",
        max_tokens=1024,
    )

    try:
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        voice = json.loads(cleaned)

        result = await db.execute(select(UserModel).where(UserModel.user_id == user.id))
        user_model = result.scalar_one_or_none()
        if not user_model:
            user_model = UserModel(user_id=user.id)
            db.add(user_model)

        user_model.voice_patterns = voice
        await db.commit()
        logger.info("Voice model rebuilt for user %s", user.id)
        return {"status": "updated", "patterns": list(voice.keys())}

    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse voice model for user %s: %s", user.id, e)
        return {"status": "error", "reason": str(e)}


async def run_all_improvement(db: AsyncSession) -> list[dict]:
    """Run improvement cycle for all Pro users."""
    from services.suggestion_service import detect_patterns

    result = await db.execute(select(User).where(User.plan == "pro"))
    users = result.scalars().all()
    results = []
    for user in users:
        logger.info("Running improvement cycle for %s", user.name)
        r = await run_improvement_cycle(user, db)

        # Detect patterns and generate proactive suggestions
        try:
            suggestions = await detect_patterns(user, db)
            if suggestions:
                r["suggestions"] = len(suggestions)
                logger.info("Generated %d skill suggestions for %s", len(suggestions), user.name)
        except Exception as e:
            logger.warning("Suggestion detection failed for %s: %s", user.name, e)

        results.append({"user_id": str(user.id), **r})

    await db.commit()
    return results


async def run_all_voice_rebuild(db: AsyncSession) -> list[dict]:
    """Run voice model rebuild for all Pro+Gmail users."""
    result = await db.execute(
        select(User).where(User.plan == "pro", User.gmail_connected == True)
    )
    users = result.scalars().all()
    results = []
    for user in users:
        logger.info("Rebuilding voice model for %s", user.name)
        r = await rebuild_voice_model(user, db)
        results.append({"user_id": str(user.id), **r})
    return results
