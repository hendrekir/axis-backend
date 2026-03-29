import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Skill, SkillExecution
from routes.auth import get_authenticated_user
from services.skill_engine import execute_skill, seed_builtin_skills

logger = logging.getLogger("axis.skills")

router = APIRouter()


# --- Pydantic models ---

class SkillCreate(BaseModel):
    name: str
    description: str | None = None
    data_sources: list[str] = []
    reasoning_model: str = "claude"
    trigger_type: str = "manual"
    trigger_config: dict = {}
    output_routing: str = "thread"
    system_prompt: str | None = None


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    data_sources: list[str] | None = None
    reasoning_model: str | None = None
    trigger_type: str | None = None
    trigger_config: dict | None = None
    output_routing: str | None = None
    system_prompt: str | None = None


class SkillChatIn(BaseModel):
    message: str


# --- CRUD ---

@router.get("/skills")
async def list_skills(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """List all skills for the current user. Seeds built-ins on first call."""
    result = await db.execute(
        select(Skill).where(Skill.user_id == user.id).order_by(Skill.created_at)
    )
    skills = result.scalars().all()

    # Seed built-in skills on first access
    if not skills:
        skills = await seed_builtin_skills(user.id, db)

    return {
        "skills": [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "is_builtin": s.is_builtin,
                "is_active": s.is_active,
                "data_sources": s.data_sources,
                "reasoning_model": s.reasoning_model,
                "trigger_type": s.trigger_type,
                "output_routing": s.output_routing,
            }
            for s in skills
        ]
    }


@router.post("/skills")
async def create_skill(
    body: SkillCreate,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom skill."""
    skill = Skill(
        user_id=user.id,
        name=body.name,
        description=body.description,
        is_builtin=False,
        data_sources=body.data_sources,
        reasoning_model=body.reasoning_model,
        trigger_type=body.trigger_type,
        trigger_config=body.trigger_config,
        output_routing=body.output_routing,
        system_prompt=body.system_prompt,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)

    return {"id": str(skill.id), "name": skill.name, "status": "created"}


@router.patch("/skills/{skill_id}")
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a skill's configuration."""
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id, Skill.user_id == user.id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    return {"id": str(skill.id), "name": skill.name, "status": "updated"}


@router.delete("/skills/{skill_id}")
async def delete_skill(
    skill_id: str,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom skill. Built-in skills can only be deactivated."""
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id, Skill.user_id == user.id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if skill.is_builtin:
        raise HTTPException(status_code=400, detail="Cannot delete built-in skill — deactivate it instead")

    await db.delete(skill)
    await db.commit()
    return {"status": "deleted"}


# --- Execution ---

@router.post("/skills/{skill_id}/run")
async def run_skill(
    skill_id: str,
    body: SkillChatIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a skill with a message."""
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id, Skill.user_id == user.id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    execution = await execute_skill(skill, user, body.message, db)
    return {
        "skill": skill.name,
        "model": execution["model"],
        "response": execution["text"],
        "elapsed_ms": execution["elapsed_ms"],
    }


# --- Legacy chat endpoint (backwards compatible) ---

@router.post("/skills/{skill_id}/chat")
async def skill_chat_post(
    skill_id: str,
    body: SkillChatIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with a skill — routes through the skills engine."""
    # Try DB skill first
    result = await db.execute(
        select(Skill).where(Skill.user_id == user.id, Skill.name == skill_id)
    )
    skill = result.scalar_one_or_none()

    # Also try by ID
    if not skill:
        result = await db.execute(
            select(Skill).where(Skill.id == skill_id, Skill.user_id == user.id)
        )
        skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found",
        )

    execution = await execute_skill(skill, user, body.message, db)
    return {"skill": skill.name, "response": execution["text"]}
