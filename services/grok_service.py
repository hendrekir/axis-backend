"""
Grok service — social trends, entertainment, breaking news, sports.

Powers the Entertainment skill. Native X/Twitter intelligence.
"""

import logging

from services.model_router import route

logger = logging.getLogger("axis.grok")

ENTERTAINMENT_SYSTEM = """You are an entertainment and social intelligence assistant.
You have native access to X/Twitter trends and social data.

Rules:
- Surface what's trending that this user would care about
- Music drops, sports scores, viral content, social buzz
- Be fun and personality-forward — not corporate
- Include specific names, scores, links where relevant
- Max 150 words
"""

SOCIAL_TRENDS_SYSTEM = """You are a social trends analyst.
Report on what's trending on X/Twitter and social media right now.

Focus on:
- Topics relevant to the user's interests
- Breaking developments
- Viral content worth knowing about
- Sentiment shifts on topics the user follows

Be specific. Include handles/names. Max 200 words.
"""

SPORTS_SYSTEM = """You are a sports intelligence assistant.
Provide scores, highlights, and relevant sports news.

Rules:
- Lead with scores and results
- Include key plays or moments
- Note upcoming fixtures relevant to the user
- Be concise — fans want facts, not fluff
- Max 150 words
"""


async def entertainment_digest(interests: list[str], user_name: str = "User") -> dict:
    """Generate an entertainment digest based on user interests."""
    interests_text = ", ".join(interests) if interests else "general entertainment"
    result = await route(
        task_type="entertainment",
        system=ENTERTAINMENT_SYSTEM,
        user_msg=f"Entertainment digest for {user_name}. Interests: {interests_text}. What's new and worth knowing?",
    )
    logger.info("Entertainment digest via %s in %dms", result["model"], result["elapsed_ms"])
    return result


async def social_trends(topics: list[str] | None = None) -> dict:
    """Get trending social content, optionally filtered by topics."""
    msg = "What's trending on social media right now?"
    if topics:
        msg += f" Focus on these topics: {', '.join(topics)}"

    result = await route(
        task_type="social_trends",
        system=SOCIAL_TRENDS_SYSTEM,
        user_msg=msg,
    )
    logger.info("Social trends via %s in %dms", result["model"], result["elapsed_ms"])
    return result


async def sports_update(teams: list[str] | None = None, leagues: list[str] | None = None) -> dict:
    """Get sports scores and news."""
    msg = "Latest sports scores and news."
    if teams:
        msg += f" Teams: {', '.join(teams)}."
    if leagues:
        msg += f" Leagues: {', '.join(leagues)}."

    result = await route(
        task_type="sports",
        system=SPORTS_SYSTEM,
        user_msg=msg,
    )
    logger.info("Sports update via %s in %dms", result["model"], result["elapsed_ms"])
    return result
