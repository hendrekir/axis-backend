from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, Task, ThreadMessage
from prompts.morning_digest import MORNING_DIGEST_PROMPT
from services.claude_service import generate
from services.push_service import send_push


async def generate_digest(user: User, db: AsyncSession) -> str:
    """Generate a morning digest for a user and store it as a thread message."""
    # Fetch active tasks
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user.id, Task.is_done == False)
        .order_by(Task.position)
        .limit(10)
    )
    tasks = result.scalars().all()
    tasks_text = "\n".join(
        f"- {t.title} ({t.category}, {'URGENT' if t.is_urgent else 'normal'})"
        for t in tasks
    ) or "No active tasks."

    # Fetch recent thread context (last 5 messages)
    result = await db.execute(
        select(ThreadMessage)
        .where(ThreadMessage.user_id == user.id)
        .order_by(ThreadMessage.created_at.desc())
        .limit(5)
    )
    recent = result.scalars().all()
    context_text = "\n".join(
        f"{m.role}: {m.content[:200]}" for m in reversed(recent)
    ) or "No recent thread history."

    prompt = MORNING_DIGEST_PROMPT.format(
        name=user.name or "there",
        mode=user.mode,
        timezone=user.timezone,
        date=datetime.now().strftime("%A, %B %d %Y"),
        tasks=tasks_text,
        recent_context=context_text,
    )

    digest = await generate(system_prompt="You are Axis, an ambient AI agent.", user_message=prompt)

    # Save digest as a thread message
    msg = ThreadMessage(
        user_id=user.id,
        role="assistant",
        content=digest,
        message_type="intel",
        source_skill="digest",
    )
    db.add(msg)
    await db.commit()

    # Send push notification if user has a device token
    if user.apns_token:
        preview = digest[:100] + "..." if len(digest) > 100 else digest
        await send_push(user.apns_token, "Morning Digest", preview)

    return digest
