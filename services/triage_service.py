"""
Triage service — cheap pre-filter using Gemini Flash-Lite ($0.01/1M tokens).

Classifies incoming items as urgent/relevant/noise before expensive models see them.
~95% of items get discarded here at near-zero cost.
"""

import json
import logging
import re

from services.model_router import route

logger = logging.getLogger("axis.triage")

TRIAGE_SYSTEM = """You are a relevance classifier for a personal AI assistant.
Your job: score every item by how important it is to THIS specific user right now.

Rules:
- urgent (7-10): needs action today, directly affects user's work/life
- relevant (4-6): interesting or useful but not time-sensitive
- noise (1-3): not relevant to this user, spam, generic content

Return ONLY a JSON array. No markdown fences. Example:
[{"id": "0", "score": 8, "class": "urgent", "reason": "client reply needs response today"}]
"""

TRIAGE_USER = """
User profile:
- Name: {name}
- Mode: {mode}
- Active tasks: {tasks}
- Today's calendar: {calendar}

Classify each item below:
{items_text}
"""


async def triage_items(
    items: list[dict],
    user_profile: dict,
) -> dict[str, list[dict]]:
    """
    Classify items as urgent/relevant/noise using Gemini Flash-Lite.

    Each item in `items` should have at minimum: { "id": str, "source": str, "summary": str }
    Returns: { "urgent": [...], "relevant": [...], "noise": [...] }
    """
    if not items:
        return {"urgent": [], "relevant": [], "noise": []}

    # Format items for the prompt
    items_text = "\n".join(
        f"[{i}] source={item.get('source', '?')} | {item.get('summary', item.get('subject', ''))}"
        for i, item in enumerate(items)
    )

    user_msg = TRIAGE_USER.format(
        name=user_profile.get("name", "User"),
        mode=user_profile.get("mode", "personal"),
        tasks=user_profile.get("tasks", "None"),
        calendar=user_profile.get("calendar", "None"),
        items_text=items_text,
    )

    result = await route(
        task_type="triage",
        system=TRIAGE_SYSTEM,
        user_msg=user_msg,
    )

    raw = result["text"]
    classifications = _parse_triage(raw, items)

    urgent = [c for c in classifications if c["class"] == "urgent"]
    relevant = [c for c in classifications if c["class"] == "relevant"]
    noise = [c for c in classifications if c["class"] == "noise"]

    logger.info(
        "Triage complete via %s: %d urgent, %d relevant, %d noise (of %d items)",
        result["model"], len(urgent), len(relevant), len(noise), len(items),
    )

    return {"urgent": urgent, "relevant": relevant, "noise": noise}


def _parse_triage(raw: str, original_items: list[dict]) -> list[dict]:
    """Parse triage JSON response, falling back gracefully."""
    # Strip markdown fences
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, list):
            parsed = [parsed]
    except json.JSONDecodeError:
        logger.warning("Triage response was not valid JSON — marking all as relevant")
        return [
            {"id": str(i), "score": 5, "class": "relevant", "reason": "triage parse failed", **item}
            for i, item in enumerate(original_items)
        ]

    # Merge classification back with original item data
    results = []
    for entry in parsed:
        idx = entry.get("id", "0")
        try:
            idx_int = int(idx)
        except (ValueError, TypeError):
            idx_int = 0

        original = original_items[idx_int] if idx_int < len(original_items) else {}
        score = entry.get("score", 5)

        # Normalize class from score if missing
        cls = entry.get("class", "")
        if not cls:
            if score >= 7:
                cls = "urgent"
            elif score >= 4:
                cls = "relevant"
            else:
                cls = "noise"

        results.append({
            **original,
            "id": str(idx),
            "score": score,
            "class": cls,
            "reason": entry.get("reason", ""),
        })

    return results
