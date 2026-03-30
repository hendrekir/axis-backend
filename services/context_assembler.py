"""
Context assembler — injects user context_notes at the top of every Claude call.

context_notes are free-form text the user writes in Settings under
"What Axis should always know". They appear BEFORE user model data
so Claude treats them as highest-priority context.
"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User, UserModel


async def assemble_context_header(user: User, db: AsyncSession) -> str:
    """Build the context header injected at the top of Claude system prompts.

    Priority order:
    1. User's context_notes (free-form, always first)
    2. User model summary (learned patterns)
    """
    parts = []

    # 1. Context notes — highest priority, user-written
    if user.context_notes and user.context_notes.strip():
        parts.append(f"IMPORTANT — What the user wants Axis to always know:\n{user.context_notes.strip()}")

    # 2. User model summary
    result = await db.execute(
        select(UserModel).where(UserModel.user_id == user.id)
    )
    model = result.scalar_one_or_none()
    if model:
        model_parts = []
        if model.voice_patterns:
            model_parts.append(f"Voice: {json.dumps(model.voice_patterns)[:200]}")
        if model.productive_windows:
            model_parts.append(f"Productive windows: {json.dumps(model.productive_windows)[:200]}")
        if model.defer_patterns:
            model_parts.append(f"Defer patterns: {json.dumps(model.defer_patterns)[:200]}")
        if model_parts:
            parts.append("Learned patterns:\n" + "\n".join(model_parts))

    return "\n\n".join(parts)
