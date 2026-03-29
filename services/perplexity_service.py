"""
Perplexity service — real-time web research and synthesis.

Powers the Research skill. Returns cited, verifiable answers.
"""

import logging

from services.model_router import route

logger = logging.getLogger("axis.perplexity")

RESEARCH_SYSTEM = """You are a research assistant powered by real-time web search.
Your job: provide thorough, cited research for the user's query.

Rules:
- Synthesise multiple sources into a clear answer
- Include specific facts, numbers, and dates
- Cite sources where possible
- Be direct — lead with the answer, then supporting detail
- If the topic is time-sensitive, prioritise the most recent information
- Max 300 words unless the query demands more depth
"""

PERSON_LOOKUP_SYSTEM = """You are a research assistant preparing a person briefing.
The user has a meeting or interaction with this person.

Provide:
- Who they are (role, company, background)
- Recent news or activity
- Relevant context for the user's interaction
- Key talking points

Be concise and factual. Max 200 words.
"""

NEWS_SYSTEM = """You are a news intelligence assistant.
Synthesise the latest news on the given topic.

Rules:
- Focus on developments from the last 24-48 hours
- Lead with the most impactful story
- Include 2-3 supporting stories if relevant
- Note any implications for the user's context
- Max 200 words
"""


async def research(query: str, user_name: str = "User") -> dict:
    """Run a general research query via Perplexity."""
    result = await route(
        task_type="research",
        system=RESEARCH_SYSTEM,
        user_msg=f"Research this for {user_name}: {query}",
    )
    logger.info("Research query completed via %s in %dms", result["model"], result["elapsed_ms"])
    return result


async def person_lookup(name: str, context: str = "") -> dict:
    """Look up a person before a meeting or interaction."""
    msg = f"Who is {name}?"
    if context:
        msg += f" Context: {context}"

    result = await route(
        task_type="person_lookup",
        system=PERSON_LOOKUP_SYSTEM,
        user_msg=msg,
    )
    logger.info("Person lookup for '%s' via %s in %dms", name, result["model"], result["elapsed_ms"])
    return result


async def news_briefing(topic: str) -> dict:
    """Get a news synthesis on a topic."""
    result = await route(
        task_type="news",
        system=NEWS_SYSTEM,
        user_msg=f"Latest news on: {topic}",
    )
    logger.info("News briefing on '%s' via %s in %dms", topic, result["model"], result["elapsed_ms"])
    return result
