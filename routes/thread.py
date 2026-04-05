import re
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Task, ThreadMessage, Note
from prompts.thread_system import AXIS_SYSTEM
from routes.auth import get_authenticated_user
from services.claude_service import chat, generate
from services.context_assembler import assemble_context_header
from services.notes_service import save_note, search_notes
from services.status_service import get_status
from services.watch_service import create_watch

# Patterns that trigger note saving
_SAVE_PATTERN = re.compile(
    r"^(remember\s|note\s(this|that)|save\s(this|that)|don't\sforget)",
    re.IGNORECASE,
)

# Patterns that trigger note recall
_RECALL_PATTERN = re.compile(
    r"(what\s(do\sI|did\sI)\s(know|say|note|save)\s(about|on|regarding)\s+)(.+)",
    re.IGNORECASE,
)

# Patterns that trigger status briefing
_STATUS_PATTERN = re.compile(
    r"(status\s+(?:of|on)\s+|update\s+on\s+|where\s+are\s+we\s+with\s+|what'?s\s+happening\s+with\s+)(.+)",
    re.IGNORECASE,
)

# Patterns that trigger watch creation
_WATCH_PATTERN = re.compile(
    r"(watch\s+|monitor\s+|let\s+me\s+know\s+if\s+|keep\s+an?\s+eye\s+on\s+|alert\s+me\s+(?:if|when)\s+)(.+?)(\s+(?:for\s+me|changes?))?$",
    re.IGNORECASE,
)

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

    # Detect note save intent
    note_saved = None
    if _SAVE_PATTERN.search(body.content):
        note_saved = await save_note(
            user_id=user.id,
            content=body.content,
            source="thread",
            context={"mode": user.mode},
            db=db,
        )

    # Detect note recall intent and fetch relevant notes
    notes_context = ""
    recall_match = _RECALL_PATTERN.search(body.content)
    if recall_match:
        topic = recall_match.group(5).strip().rstrip("?.")
        found = await search_notes(user.id, topic, db, limit=5)
        if found:
            notes_context = "Relevant saved notes:\n" + "\n".join(
                f"- {n['content']}" for n in found
            )
        else:
            notes_context = f"No saved notes found about '{topic}'."

    # Detect status intent
    status_match = _STATUS_PATTERN.search(body.content)
    if status_match:
        topic = status_match.group(2).strip().rstrip("?.")
        briefing = await get_status(user, topic, db)
        notes_context = (notes_context + "\n\n" if notes_context else "") + \
            f"Status briefing for '{topic}':\n{briefing}"

    # Detect watch intent
    watch_created = None
    watch_match = _WATCH_PATTERN.search(body.content)
    if watch_match and not status_match and not note_saved:
        topic = watch_match.group(2).strip().rstrip("?.")
        watch_created = await create_watch(
            user_id=user.id, topic=topic, db=db,
        )
        notes_context = (notes_context + "\n\n" if notes_context else "") + \
            f"[You just created a watch on \"{topic}\". It will be checked hourly. Confirm to the user.]"

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

    # Add note-saved context for Claude
    if note_saved:
        notes_context = (notes_context + "\n" if notes_context else "") + \
            f"[You just saved a note: \"{note_saved.content}\". Confirm to the user.]"

    # Assemble full context header (context_notes + user model)
    context_header = await assemble_context_header(user, db)
    full_notes_context = "\n\n".join(filter(None, [context_header, notes_context]))

    # Build system prompt
    system = AXIS_SYSTEM.format(
        name=user.name or "there",
        mode=user.mode,
        top_tasks=tasks_str,
        notes_context=full_notes_context,
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
            "role": user_msg.role,
            "content": user_msg.content,
            "message_type": user_msg.message_type,
            "source_skill": user_msg.source_skill,
            "created_at": user_msg.created_at.isoformat() if user_msg.created_at else "",
        },
        "response": {
            "id": str(assistant_msg.id),
            "role": assistant_msg.role,
            "content": assistant_msg.content,
            "message_type": assistant_msg.message_type,
            "source_skill": assistant_msg.source_skill,
            "created_at": assistant_msg.created_at.isoformat() if assistant_msg.created_at else "",
        },
    }


@router.post("/dream")
async def dream_compress(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Compress thread into a context summary note and archive messages."""
    # Fetch last 50 non-archived messages
    result = await db.execute(
        select(ThreadMessage)
        .where(
            ThreadMessage.user_id == user.id,
            ThreadMessage.archived == False,
        )
        .order_by(ThreadMessage.created_at.desc())
        .limit(50)
    )
    messages = list(reversed(result.scalars().all()))

    if not messages:
        return {"summary": None, "archived_count": 0}

    # Build conversation text for Claude
    conversation = "\n".join(
        f"[{m.role}] {m.content}" for m in messages
    )

    summary = await generate(
        system_prompt=(
            "You are Axis. Compress this conversation thread into a concise context summary. "
            "Extract: key decisions made, commitments given, open loops, important facts learned, "
            "and any action items. Write in third person about the user. "
            "Be specific — names, dates, amounts. No filler. Max 300 words."
        ),
        user_message=conversation,
        max_tokens=512,
    )

    # Save summary as a dream note
    note = Note(
        user_id=user.id,
        content=summary,
        source="dream",
        tags=["dream", "context-compression"],
        context_snapshot={"message_count": len(messages), "compressed_at": datetime.utcnow().isoformat()},
    )
    db.add(note)

    # Archive all fetched messages
    for m in messages:
        m.archived = True

    await db.commit()

    return {"summary": summary, "archived_count": len(messages)}


@router.get("/history")
async def get_history(
    limit: int = 50,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Get thread message history."""
    result = await db.execute(
        select(ThreadMessage)
        .where(ThreadMessage.user_id == user.id, ThreadMessage.archived == False)
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
