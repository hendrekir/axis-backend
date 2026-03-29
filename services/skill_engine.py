"""
Skill engine — executes skills through the multi-model router.

Each skill has its own system prompt, data sources, and reasoning model.
The engine assembles context, calls the right model, logs the execution.
"""

import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Skill, SkillExecution, User
from services.model_router import route

logger = logging.getLogger("axis.skill_engine")

# Built-in skill definitions seeded on first access
BUILTIN_SKILLS = [
    {
        "name": "email",
        "description": "Email Intelligence — ranks inbox, drafts replies in your voice",
        "data_sources": ["gmail"],
        "reasoning_model": "claude",
        "trigger_type": "dispatch",
        "output_routing": "thread",
        "system_prompt": (
            "You are Axis, acting as {name}'s email intelligence.\n"
            "Mode: {mode}. Analyse the email and provide actionable insight.\n"
            "If a reply is needed, draft it in the user's voice. Keep under 80 words."
        ),
    },
    {
        "name": "calendar",
        "description": "Calendar Intelligence — meeting prep, conflict detection, travel time",
        "data_sources": ["google_calendar"],
        "reasoning_model": "claude",
        "trigger_type": "dispatch",
        "output_routing": "thread",
        "system_prompt": (
            "You are Axis, acting as {name}'s calendar intelligence.\n"
            "Mode: {mode}. Analyse upcoming events. Flag conflicts, suggest prep.\n"
            "Keep under 80 words."
        ),
    },
    {
        "name": "finance",
        "description": "Finance Intelligence — invoice alerts, cash flow, overdue detection",
        "data_sources": ["stripe", "xero"],
        "reasoning_model": "claude",
        "trigger_type": "dispatch",
        "output_routing": "push",
        "system_prompt": (
            "You are Axis, acting as {name}'s finance intelligence.\n"
            "Mode: {mode}. Analyse financial data. Flag overdue invoices, cash flow issues.\n"
            "Keep under 80 words."
        ),
    },
    {
        "name": "research",
        "description": "Research Intelligence — real-time web research and synthesis",
        "data_sources": ["perplexity"],
        "reasoning_model": "perplexity",
        "trigger_type": "manual",
        "output_routing": "thread",
        "system_prompt": (
            "You are a research assistant for {name}.\n"
            "Provide thorough, cited research. Synthesise multiple sources.\n"
            "Be specific and actionable."
        ),
    },
    {
        "name": "entertainment",
        "description": "Entertainment Intelligence — music, social trends, sports, news",
        "data_sources": ["spotify", "reddit", "x_twitter"],
        "reasoning_model": "grok",
        "trigger_type": "dispatch",
        "output_routing": "digest",
        "system_prompt": (
            "You are Axis, curating entertainment for {name}.\n"
            "Mode: {mode}. Surface what's new and relevant to their interests.\n"
            "Keep it fun, brief, and specific. Max 60 words."
        ),
    },
    {
        "name": "site",
        "description": "Site Intelligence — builder mode for construction, suppliers, inspections",
        "data_sources": ["gmail", "google_calendar"],
        "reasoning_model": "claude",
        "trigger_type": "dispatch",
        "output_routing": "push",
        "system_prompt": (
            "You are Axis in Builder mode for {name}.\n"
            "Focus on site operations: suppliers, inspections, crew, materials.\n"
            "Be direct and practical. Keep under 80 words."
        ),
    },
]


async def seed_builtin_skills(user_id, db: AsyncSession) -> list[Skill]:
    """Create built-in skills for a new user. Returns the created skills."""
    skills = []
    for defn in BUILTIN_SKILLS:
        skill = Skill(
            user_id=user_id,
            name=defn["name"],
            description=defn["description"],
            is_builtin=True,
            is_active=True,
            data_sources=defn["data_sources"],
            reasoning_model=defn["reasoning_model"],
            trigger_type=defn["trigger_type"],
            trigger_config={},
            output_routing=defn["output_routing"],
            system_prompt=defn["system_prompt"],
        )
        db.add(skill)
        skills.append(skill)

    await db.commit()
    for s in skills:
        await db.refresh(s)

    logger.info("Seeded %d built-in skills for user %s", len(skills), user_id)
    return skills


async def execute_skill(
    skill: Skill,
    user: User,
    user_message: str,
    db: AsyncSession,
) -> dict:
    """Execute a single skill through the model router. Returns { text, model, elapsed_ms }."""
    # Build system prompt with user context
    system = (skill.system_prompt or "You are Axis, a helpful AI assistant.").format(
        name=user.name or "there",
        mode=user.mode,
    )

    # Route to the skill's configured model
    result = await route(
        task_type=skill.name,
        system=system,
        user_msg=user_message,
        model_override=skill.reasoning_model,
    )

    # Log execution
    execution = SkillExecution(
        skill_id=skill.id,
        user_id=user.id,
        input_context={"message": user_message},
        output_result=result["text"][:2000],
        model_used=result["model"],
        surface_delivered=skill.output_routing,
        execution_time_ms=result["elapsed_ms"],
    )
    db.add(execution)
    await db.commit()

    logger.info(
        "Skill '%s' executed via %s in %dms for user %s",
        skill.name, result["model"], result["elapsed_ms"], user.id,
    )

    return result


async def run_dispatch_skills(user: User, db: AsyncSession) -> list[dict]:
    """Run all dispatch-triggered active skills for a user. Called by the dispatch job."""
    result = await db.execute(
        select(Skill).where(
            Skill.user_id == user.id,
            Skill.is_active == True,
            Skill.trigger_type == "dispatch",
        )
    )
    skills = result.scalars().all()

    results = []
    for skill in skills:
        try:
            # Build a context message for the skill based on its data sources
            context_msg = f"Run your {skill.name} analysis. Current mode: {user.mode}."
            execution = await execute_skill(skill, user, context_msg, db)
            results.append({
                "skill": skill.name,
                "model": execution["model"],
                "output_routing": skill.output_routing,
                "text": execution["text"],
                "elapsed_ms": execution["elapsed_ms"],
            })
        except Exception as e:
            logger.error("Skill '%s' failed for user %s: %s", skill.name, user.id, e)
            results.append({"skill": skill.name, "error": str(e)})

    return results
