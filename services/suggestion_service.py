"""
Proactive skill suggestion service — detects repeated patterns
and suggests automation.

Called during the Sunday improvement cycle. Analyses 30 days of
interactions to find repeating behaviours that could be automated.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Interaction, SkillSuggestion, ThreadMessage, User
from services.claude_service import generate

logger = logging.getLogger("axis.suggestions")

SUGGESTION_SYSTEM = """You are Axis noticing a repeated pattern in the user's behaviour.
Write a natural, warm, one-sentence suggestion. Examples:

"I noticed you've researched council compliance three times this week. Want me to add a daily briefing on this to your morning digest?"
"You've manually chased invoices from 4 different suppliers. I could automate follow-up reminders — want me to set that up?"

Pattern detected: {pattern}
Frequency: {count} times in the last 30 days
Content type: {content_type}

Return ONLY the suggestion sentence. No quotes, no explanation.
"""


async def detect_patterns(user: User, db: AsyncSession) -> list[dict]:
    """Analyse 30 days of interactions for repeating patterns."""
    cutoff = datetime.utcnow() - timedelta(days=30)

    # Group interactions by content_type + action
    result = await db.execute(
        select(
            Interaction.content_type,
            Interaction.action_taken,
            func.count().label("count"),
        )
        .where(
            Interaction.user_id == user.id,
            Interaction.created_at >= cutoff,
            Interaction.action_taken.in_(["surfaced", "correction", "research"]),
        )
        .group_by(Interaction.content_type, Interaction.action_taken)
        .having(func.count() >= 3)
    )
    patterns = result.all()

    if not patterns:
        return []

    # Check existing suggestions to avoid duplicates
    result = await db.execute(
        select(SkillSuggestion.pattern_detected)
        .where(
            SkillSuggestion.user_id == user.id,
            SkillSuggestion.suggested_at >= cutoff,
        )
    )
    existing = {row[0] for row in result.all()}

    suggestions = []
    for content_type, action, count in patterns:
        pattern_key = f"{content_type}:{action}"
        if pattern_key in existing:
            continue

        # Special case: invoice chasing
        if "invoice" in (content_type or "").lower() and count >= 3:
            pattern_desc = f"manually handled invoices {count} times"
        else:
            pattern_desc = f"{action} on {content_type} {count} times in 30 days"

        # Generate natural suggestion via Claude
        prompt = SUGGESTION_SYSTEM.format(
            pattern=pattern_desc,
            count=count,
            content_type=content_type,
        )
        suggestion_text = await generate(
            system_prompt="You are Axis. Return only the suggestion sentence.",
            user_message=prompt,
            max_tokens=128,
        )
        suggestion_text = suggestion_text.strip().strip('"')

        # Infer a skill name
        suggested_name = f"{content_type} automation" if content_type else "pattern automation"

        # Save suggestion
        suggestion = SkillSuggestion(
            user_id=user.id,
            pattern_detected=pattern_key,
            suggested_name=suggested_name,
            suggested_config={
                "content_type": content_type,
                "action": action,
                "frequency": count,
                "suggestion_text": suggestion_text,
            },
        )
        db.add(suggestion)

        # Surface as thread message
        msg = ThreadMessage(
            user_id=user.id,
            role="assistant",
            content=suggestion_text,
            message_type="suggestion",
            source_skill="apprentice",
        )
        db.add(msg)

        suggestions.append({
            "pattern": pattern_key,
            "suggestion": suggestion_text,
            "count": count,
        })

        logger.info(
            "Skill suggestion for %s: %s (%d occurrences)",
            user.name, pattern_key, count,
        )

    return suggestions
