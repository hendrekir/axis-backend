from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Task, ThreadMessage
from prompts.thread_system import AXIS_SYSTEM
from routes.auth import get_authenticated_user
from services.claude_service import chat

router = APIRouter()


class ThreadMessageIn(BaseModel):
    content: str


class ThreadMessageOut(BaseModel):
    id: str
    role: str
    content: str
    message_type: str
    source_skill: str | None
    created_at: str


@router.post("")
async def send_message(
    body: ThreadMessageIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message in the thread and get Axis's response."""
    # Save user message
    user_msg = ThreadMessage(
        user_id=user.id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    # Fetch recent thread history for context
    result = await db.execute(
        select(ThreadMessage)
        .where(ThreadMessage.user_id == user.id)
        .order_by(ThreadMessage.created_at.desc())
        .limit(20)
    )
    history = list(reversed(result.scalars().all()))

    # Fetch top 3 tasks for system prompt context
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user.id, Task.is_done == False)
        .order_by(Task.position)
        .limit(3)
    )
    top_tasks = result.scalars().all()
    tasks_str = ", ".join(t.title for t in top_tasks) or "None set"

    # Build system prompt
    system = AXIS_SYSTEM.format(
        name=user.name or "there",
        mode=user.mode,
        energy="normal",
        top_tasks=tasks_str,
        recent_context="Thread conversation in progress.",
    )

    # Build messages array for Claude
    messages = [
        {"role": m.role, "content": m.content}
        for m in history
    ]

    # Get Axis response
    response_text = await chat(system_prompt=system, messages=messages)

    # Save assistant response
    assistant_msg = ThreadMessage(
        user_id=user.id,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)
    await db.commit()

    return {
        "user_message": {
            "id": str(user_msg.id),
            "content": user_msg.content,
        },
        "response": {
            "id": str(assistant_msg.id),
            "content": assistant_msg.content,
            "message_type": assistant_msg.message_type,
        },
    }


@router.get("/history")
async def get_history(
    limit: int = 50,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Get thread message history."""
    result = await db.execute(
        select(ThreadMessage)
        .where(ThreadMessage.user_id == user.id)
        .order_by(ThreadMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "message_type": m.message_type,
            "source_skill": m.source_skill,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(messages)
    ]
