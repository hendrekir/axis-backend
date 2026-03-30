"""
Notes service — save, search, and relate smart notes.

Notes are created from thread messages ("remember X"), brain dumps,
dispatch insights, or manual POST /notes. Full-text search via
Postgres GIN index on to_tsvector('english', content).
"""

import logging
import re

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import Note, Task, ThreadMessage

logger = logging.getLogger("axis.notes")

# Prefixes users might type before the actual note content
_STRIP_PREFIXES = re.compile(
    r"^(remember\s*(?:this|that)?[:.]?\s*|note\s*(?:this|that)?[:.]?\s*)",
    re.IGNORECASE,
)


def _clean_content(raw: str) -> str:
    """Strip 'remember this:' / 'note that:' prefixes."""
    return _STRIP_PREFIXES.sub("", raw).strip()


def _auto_tags(content: str) -> list[str]:
    """Extract simple entity-style tags from content."""
    tags = []
    lowered = content.lower()

    # Detect common categories
    category_keywords = {
        "finance": ["invoice", "payment", "budget", "cash", "revenue", "expense", "stripe", "xero"],
        "email": ["email", "reply", "inbox", "gmail", "marcus", "sent"],
        "meeting": ["meeting", "call", "standup", "sync", "agenda"],
        "site": ["site", "builder", "supplier", "membrane", "concrete", "inspection"],
        "health": ["sleep", "exercise", "steps", "hrv", "energy"],
        "deadline": ["deadline", "due", "overdue", "by friday", "by monday", "by end of"],
    }
    for tag, keywords in category_keywords.items():
        if any(kw in lowered for kw in keywords):
            tags.append(tag)

    # Extract @mentions as tags
    mentions = re.findall(r"@(\w+)", content)
    tags.extend(mentions)

    return tags[:10]  # Cap at 10


async def save_note(
    user_id,
    content: str,
    source: str = "thread",
    context: dict | None = None,
    db: AsyncSession = None,
) -> Note:
    """Save a note with auto-generated tags."""
    cleaned = _clean_content(content)
    tags = _auto_tags(cleaned)

    note = Note(
        user_id=user_id,
        content=cleaned,
        tags=tags,
        source=source,
        context_snapshot=context or {},
    )
    db.add(note)
    await db.flush()

    logger.info("Note saved for user %s: %s (tags: %s)", user_id, cleaned[:60], tags)
    return note


async def search_notes(
    user_id,
    query: str,
    db: AsyncSession,
    limit: int = 20,
) -> list[dict]:
    """Full-text search + tag search on user notes."""
    results = []

    # Full-text search using Postgres ts_vector
    fts_query = text("""
        SELECT id, content, tags, source, created_at,
               ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) AS rank
        FROM notes
        WHERE user_id = :user_id
          AND to_tsvector('english', content) @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :limit
    """)

    rows = await db.execute(fts_query, {"user_id": user_id, "query": query, "limit": limit})
    for row in rows:
        results.append({
            "id": str(row.id),
            "content": row.content,
            "tags": row.tags or [],
            "source": row.source,
            "rank": float(row.rank),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    # Also search by tag if query looks like a single word
    if not results and len(query.split()) == 1:
        tag_query = text("""
            SELECT id, content, tags, source, created_at
            FROM notes
            WHERE user_id = :user_id AND :tag = ANY(tags)
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        rows = await db.execute(tag_query, {"user_id": user_id, "tag": query.lower(), "limit": limit})
        for row in rows:
            results.append({
                "id": str(row.id),
                "content": row.content,
                "tags": row.tags or [],
                "source": row.source,
                "rank": 0.5,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            })

    return results


async def get_related_notes(
    user_id,
    topic: str,
    db: AsyncSession,
    limit: int = 10,
) -> dict:
    """Get notes + related emails + tasks on the same topic."""
    # Notes matching the topic
    notes = await search_notes(user_id, topic, db, limit=limit)

    # Tasks matching the topic
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == user_id,
            func.lower(Task.title).contains(topic.lower()),
        )
        .order_by(Task.created_at.desc())
        .limit(5)
    )
    tasks = [
        {
            "id": str(t.id),
            "title": t.title,
            "category": t.category,
            "is_done": t.is_done,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in result.scalars().all()
    ]

    # Thread messages mentioning the topic
    result = await db.execute(
        select(ThreadMessage)
        .where(
            ThreadMessage.user_id == user_id,
            func.lower(ThreadMessage.content).contains(topic.lower()),
        )
        .order_by(ThreadMessage.created_at.desc())
        .limit(5)
    )
    thread_mentions = [
        {
            "role": m.role,
            "content": m.content[:200],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in result.scalars().all()
    ]

    return {
        "notes": notes,
        "related_tasks": tasks,
        "thread_mentions": thread_mentions,
    }
