"""
Signal filter — 5-layer noise reduction applied after triage.

1. Relevance: connects to something user demonstrably cares about
2. Urgency: score 1-10, below threshold = digest or silent
3. Context: relevant to current calendar/location/mode
4. Deduplication: same story shown once, best source wins (24hr window)
5. Apprentice: 8+ dismissals from a topic = auto-deprioritise
"""

import logging
from datetime import datetime, timedelta
from hashlib import sha256

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Interaction, Task, UserModel

logger = logging.getLogger("axis.signal_filter")

# Items with urgency below this go to digest or silent
URGENCY_PUSH_THRESHOLD = 7
URGENCY_DIGEST_THRESHOLD = 4

# Consecutive dismissals before auto-deprioritise
APPRENTICE_DISMISS_THRESHOLD = 8

# Dedup window
DEDUP_HOURS = 24


async def apply_filters(
    items: list[dict],
    user_id,
    user_mode: str,
    db: AsyncSession,
) -> dict[str, list[dict]]:
    """
    Apply all 5 signal filters to triaged items.

    Input: items from triage (each has score, class, source, summary, reason).
    Output: { "push": [...], "digest": [...], "silent": [...] }
    """
    if not items:
        return {"push": [], "digest": [], "silent": []}

    # Load user context for filters
    user_model = await _load_user_model(user_id, db)
    active_tasks = await _load_active_tasks(user_id, db)
    dismiss_counts = await _load_dismiss_counts(user_id, db)

    seen_keys: set[str] = set()
    push, digest, silent = [], [], []

    for item in items:
        score = item.get("score", 5)
        source = item.get("source", "")
        summary = item.get("summary", item.get("subject", ""))

        # Filter 1 — Relevance: boost if connects to active tasks or user interests
        relevance_boost = _relevance_boost(summary, active_tasks, user_model)
        score = min(10, score + relevance_boost)

        # Filter 2 — Urgency: already scored by triage, apply threshold routing
        # (score is used for routing below)

        # Filter 3 — Context: boost if matches current mode
        if _matches_mode(item, user_mode):
            score = min(10, score + 1)

        # Filter 4 — Deduplication: skip if same content seen in window
        dedup_key = _dedup_key(summary)
        if dedup_key in seen_keys:
            item["score"] = score
            item["filter_reason"] = "duplicate"
            silent.append(item)
            continue
        seen_keys.add(dedup_key)

        # Filter 5 — Apprentice: deprioritise if user repeatedly dismisses this type
        topic = item.get("category", source)
        if dismiss_counts.get(topic, 0) >= APPRENTICE_DISMISS_THRESHOLD:
            score = max(1, score - 3)
            item["apprentice_deprioritised"] = True

        # Route based on final score
        item["score"] = score
        if score >= URGENCY_PUSH_THRESHOLD:
            push.append(item)
        elif score >= URGENCY_DIGEST_THRESHOLD:
            digest.append(item)
        else:
            silent.append(item)

    logger.info(
        "Signal filter: %d push, %d digest, %d silent (from %d items)",
        len(push), len(digest), len(silent), len(items),
    )

    return {"push": push, "digest": digest, "silent": silent}


def _relevance_boost(summary: str, active_tasks: list[str], user_model: dict) -> int:
    """Boost score if summary keywords overlap with active tasks or user interests."""
    summary_lower = summary.lower()
    boost = 0

    # Check against active task titles
    for task_title in active_tasks:
        words = [w for w in task_title.lower().split() if len(w) > 3]
        if any(w in summary_lower for w in words):
            boost = 2
            break

    # Check against user model interests (if populated)
    interests = user_model.get("interests", [])
    if isinstance(interests, list):
        for interest in interests:
            if interest.lower() in summary_lower:
                boost = max(boost, 1)
                break

    return boost


def _matches_mode(item: dict, user_mode: str) -> bool:
    """Check if item category aligns with current mode."""
    mode_categories = {
        "work": {"work", "finance", "email", "meeting", "invoice"},
        "builder": {"work", "site", "supplier", "inspection", "construction"},
        "personal": {"health", "family", "home", "personal"},
        "student": {"study", "research", "assignment", "lecture"},
        "founder": {"work", "finance", "investor", "product", "hiring"},
    }
    relevant = mode_categories.get(user_mode, set())
    item_cat = item.get("category", "").lower()
    item_source = item.get("source", "").lower()
    return item_cat in relevant or item_source in relevant


def _dedup_key(text: str) -> str:
    """Generate a short hash for deduplication. Normalise whitespace first."""
    normalised = " ".join(text.lower().split())
    return sha256(normalised.encode()).hexdigest()[:16]


async def _load_user_model(user_id, db: AsyncSession) -> dict:
    """Load user_model JSON fields for relevance checking."""
    result = await db.execute(
        select(UserModel).where(UserModel.user_id == user_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        return {}
    return {
        "interests": model.productive_windows.get("interests", []) if model.productive_windows else [],
        "defer_patterns": model.defer_patterns or {},
    }


async def _load_active_tasks(user_id, db: AsyncSession) -> list[str]:
    """Load active task titles for relevance matching."""
    result = await db.execute(
        select(Task.title)
        .where(Task.user_id == user_id, Task.is_done == False)
        .limit(20)
    )
    return [row[0] for row in result.all()]


async def _load_dismiss_counts(user_id, db: AsyncSession) -> dict[str, int]:
    """Count recent dismissals per content_type for apprentice filter."""
    cutoff = datetime.utcnow() - timedelta(days=14)
    result = await db.execute(
        select(Interaction.content_type, func.count())
        .where(
            Interaction.user_id == user_id,
            Interaction.action_taken == "dismissed",
            Interaction.created_at >= cutoff,
        )
        .group_by(Interaction.content_type)
    )
    return {row[0]: row[1] for row in result.all()}
