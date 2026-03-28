import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Task
from prompts.brain_dump import BRAIN_DUMP_PROMPT
from routes.auth import get_authenticated_user
from services.claude_service import generate

router = APIRouter()


class BrainDumpIn(BaseModel):
    text: str


def parse_tasks(response: str) -> list[dict]:
    """Parse Claude's TASK: lines into structured task dicts."""
    tasks = []
    for line in response.strip().split("\n"):
        match = re.match(
            r"TASK:\s*(.+?)\s*\|\s*CAT:\s*(\w+)\s*\|\s*WHY:\s*(.+?)\s*\|\s*URGENT:\s*(true|false)",
            line.strip(),
            re.IGNORECASE,
        )
        if match:
            tasks.append({
                "title": match.group(1).strip(),
                "category": match.group(2).strip().lower(),
                "why": match.group(3).strip(),
                "is_urgent": match.group(4).strip().lower() == "true",
            })
    return tasks


def extract_summary(response: str, task_count: int) -> str:
    """Extract the summary text after the TASK lines."""
    lines = response.strip().split("\n")
    non_task_lines = [
        l.strip() for l in lines
        if l.strip() and not l.strip().upper().startswith("TASK:")
    ]
    return " ".join(non_task_lines[-2:]) if non_task_lines else ""


@router.post("/brain-dump")
async def brain_dump(
    body: BrainDumpIn,
    db: AsyncSession = Depends(get_db),
):
    """Process a brain dump — extract and rank tasks from free-form text."""
    # TODO: restore auth — user: User = Depends(get_authenticated_user)
    prompt = BRAIN_DUMP_PROMPT.format(dump_text=body.text)

    response_text = await generate(
        system_prompt="You are Axis, an ambient AI agent. Extract and rank tasks.",
        user_message=prompt,
    )

    # Parse structured tasks from response
    parsed_tasks = parse_tasks(response_text)
    summary = extract_summary(response_text, len(parsed_tasks))

    return {
        "tasks": [
            {
                "title": t["title"],
                "category": t["category"],
                "why": t["why"],
                "is_urgent": t["is_urgent"],
                "position": i,
            }
            for i, t in enumerate(parsed_tasks)
        ],
        "summary": summary,
        "raw_response": response_text,
    }
