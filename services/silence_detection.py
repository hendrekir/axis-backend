"""
Silence-as-signal detection.

Runs as part of the Sunday 3AM improvement job.
For each user:
1. Pull thread_messages and journal_entries from last 30 days
2. Call Claude to extract entity mentions (names, projects, companies) per week
3. Compare week 1-3 mention frequency vs week 4
4. Entities mentioned 3+ times in weeks 1-3 and 0 times in week 4 = silence signal
5. Create dispatched_signals rows for each detected silence
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    User, ThreadMessage, JournalEntry,
    DispatchedSignal, AgentActivity,
)
from services.claude_service import generate

logger = logging.getLogger("axis.silence")

ENTITY_EXTRACT_SYSTEM = """Extract every named entity from these messages.
Return JSON only, no markdown fences:
{
  "entities": [
    {"name": "exact name or project", "type": "person" | "project" | "company", "count": <times mentioned>}
  ]
}
Rules:
- Only include proper nouns — real people, specific projects, specific companies.
- Merge obvious variants (e.g. "Josh" and "Joshua" = one entity).
- Ignore generic words, common nouns, app names (Gmail, Axis, etc).
- Count each distinct mention.
Return valid JSON only.
"""


async def detect_silence_signals(user: User, db: AsyncSession) -> list[dict]:
    """Detect entities that have gone silent in the last week vs prior 3 weeks."""
    now = datetime.utcnow()
    cutoff_30d = now - timedelta(days=30)
    cutoff_7d = now - timedelta(days=7)

    # Pull thread messages from last 30 days
    result = await db.execute(
        select(ThreadMessage)
        .where(
            ThreadMessage.user_id == user.id,
            ThreadMessage.created_at >= cutoff_30d,
        )
        .order_by(ThreadMessage.created_at.asc())
    )
    messages = result.scalars().all()

    # Pull journal entries from last 30 days
    result = await db.execute(
        select(JournalEntry)
        .where(
            JournalEntry.user_id == user.id,
            JournalEntry.created_at >= cutoff_30d,
        )
        .order_by(JournalEntry.created_at.asc())
    )
    journals = result.scalars().all()

    if not messages and not journals:
        return []

    # Bucket into weeks 1-3 (days 8-30 ago) and week 4 (last 7 days)
    early_texts = []
    recent_texts = []
    for m in messages:
        text = m.content[:300]
        if m.created_at < cutoff_7d:
            early_texts.append(text)
        else:
            recent_texts.append(text)
    for j in journals:
        text = f"{j.question}: {j.answer}"[:300]
        if j.created_at < cutoff_7d:
            early_texts.append(text)
        else:
            recent_texts.append(text)

    if not early_texts:
        return []

    # Extract entities from weeks 1-3
    early_chunk = "\n---\n".join(early_texts[:80])
    early_entities = await _extract_entities(early_chunk)

    # Extract entities from week 4
    recent_entities: dict[str, int] = {}
    if recent_texts:
        recent_chunk = "\n---\n".join(recent_texts[:40])
        recent_entities = await _extract_entities(recent_chunk)

    # Compare: 3+ mentions in weeks 1-3, 0 in week 4 = silence
    signals = []
    for name, info in early_entities.items():
        if info["count"] >= 3 and name.lower() not in {k.lower() for k in recent_entities}:
            signals.append({
                "entity": name,
                "type": info["type"],
                "early_count": info["count"],
            })

    # Create dispatched signals and log
    created = []
    for sig in signals:
        signal_key = f"silence:{sig['entity'].lower().replace(' ', '_')}"

        # Check if already dispatched recently (7 days)
        existing = await db.execute(
            select(DispatchedSignal).where(
                and_(
                    DispatchedSignal.user_id == user.id,
                    DispatchedSignal.signal_key == signal_key,
                    DispatchedSignal.dispatched_at >= cutoff_7d,
                )
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Upsert dispatched signal
        result = await db.execute(
            select(DispatchedSignal).where(
                DispatchedSignal.user_id == user.id,
                DispatchedSignal.signal_key == signal_key,
            )
        )
        ds = result.scalar_one_or_none()
        entity_type = sig["type"]
        title = f"{sig['entity']} has gone quiet"
        subtitle = (
            f"Mentioned {sig['early_count']} times in the last month, "
            f"0 times this week"
        )

        if ds:
            ds.surface = "notification"
            ds.urgency = 6
            ds.dispatched_at = now
            ds.title = title
            ds.subtitle = subtitle
            ds.action_type = "follow_up"
            ds.completed = False
            ds.dismissed = False
            ds.snoozed_until = None
        else:
            ds = DispatchedSignal(
                user_id=user.id,
                signal_key=signal_key,
                surface="notification",
                urgency=6,
                title=title,
                subtitle=subtitle,
                action_type="follow_up",
            )
            db.add(ds)

        created.append({
            "entity": sig["entity"],
            "type": entity_type,
            "early_count": sig["early_count"],
            "signal_key": signal_key,
        })

    if created:
        db.add(AgentActivity(
            user_id=user.id,
            skill="silence_detection",
            action="signals_created",
            detail=f"{len(created)} silence signals detected",
            result=json.dumps([c["entity"] for c in created])[:500],
        ))
        await db.commit()
        logger.info(
            "Silence detection for %s: %d signals — %s",
            user.name, len(created),
            ", ".join(c["entity"] for c in created),
        )

    return created


async def _extract_entities(text_block: str) -> dict[str, dict]:
    """Call Claude to extract named entities with counts from a text block."""
    raw = await generate(
        system_prompt=ENTITY_EXTRACT_SYSTEM,
        user_message=text_block,
        max_tokens=1024,
    )

    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip())
    cleaned = re.sub(r'\n?```\s*$', '', cleaned)

    try:
        parsed = json.loads(cleaned)
        entities = parsed.get("entities", [])
    except (json.JSONDecodeError, TypeError):
        logger.warning("Entity extraction returned invalid JSON: %s", raw[:200])
        return {}

    result: dict[str, dict] = {}
    for e in entities:
        name = (e.get("name") or "").strip()
        if not name or len(name) < 2:
            continue
        count = int(e.get("count", 1))
        etype = e.get("type", "unknown")
        # Merge by lowercase key, keep the cased version with highest count
        key = name.lower()
        if key in result:
            result[key]["count"] += count
        else:
            result[key] = {"name": name, "type": etype, "count": count}

    # Return with original casing as keys
    return {v["name"]: {"type": v["type"], "count": v["count"]} for v in result.values()}
