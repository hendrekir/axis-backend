from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User
from routes.auth import get_authenticated_user
from services.claude_service import generate
from prompts.skills.email_skill import EMAIL_SKILL_PROMPT
from prompts.skills.calendar_skill import CALENDAR_SKILL_PROMPT
from prompts.skills.finance_skill import FINANCE_SKILL_PROMPT
from prompts.skills.site_skill import SITE_SKILL_PROMPT
from prompts.skills.study_skill import STUDY_SKILL_PROMPT
from prompts.skills.team_skill import TEAM_SKILL_PROMPT

router = APIRouter()

SKILL_PROMPTS = {
    "email": EMAIL_SKILL_PROMPT,
    "calendar": CALENDAR_SKILL_PROMPT,
    "finance": FINANCE_SKILL_PROMPT,
    "site": SITE_SKILL_PROMPT,
    "study": STUDY_SKILL_PROMPT,
    "team": TEAM_SKILL_PROMPT,
}

# Default context values for skill prompts that need extra params
SKILL_DEFAULTS = {
    "site": {"site_context": "No active site"},
    "calendar": {"timezone": "Australia/Brisbane"},
    "team": {"team_size": "0"},
}


class SkillChatIn(BaseModel):
    message: str


@router.get("/skills/{skill_id}/chat")
async def skill_chat_get(
    skill_id: str,
    message: str,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Talk to a specific skill (GET with query param)."""
    return await _handle_skill_chat(skill_id, message, user)


@router.post("/skills/{skill_id}/chat")
async def skill_chat_post(
    skill_id: str,
    body: SkillChatIn,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Talk to a specific skill (POST with body)."""
    return await _handle_skill_chat(skill_id, body.message, user)


async def _handle_skill_chat(skill_id: str, message: str, user: User) -> dict:
    prompt_template = SKILL_PROMPTS.get(skill_id)
    if not prompt_template:
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_id}' not found. Available: {list(SKILL_PROMPTS.keys())}",
        )

    # Build format kwargs
    fmt = {
        "name": user.name or "there",
        "mode": user.mode,
    }
    if skill_id in SKILL_DEFAULTS:
        fmt.update(SKILL_DEFAULTS[skill_id])

    system = prompt_template.format(**fmt)
    response = await generate(system_prompt=system, user_message=message)

    return {
        "skill": skill_id,
        "response": response,
    }
