import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Task
from routes.auth import get_authenticated_user

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    category: str  # work | health | home | money | family | admin | personal
    due: str | None = None
    is_urgent: bool = False
    why: str | None = None
    position: int = 0


class TaskUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    due: str | None = None
    is_urgent: bool | None = None
    is_done: bool | None = None
    position: int | None = None


@router.get("/signal")
async def get_signal(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current top 3 tasks (the user's signal)."""
    result = await db.execute(
        select(Task)
        .where(Task.user_id == user.id, Task.is_done == False)
        .order_by(Task.position)
        .limit(3)
    )
    tasks = result.scalars().all()
    return {
        "signal": [
            {
                "id": str(t.id),
                "title": t.title,
                "category": t.category,
                "due": t.due,
                "is_urgent": t.is_urgent,
                "why": t.why,
                "position": t.position,
            }
            for t in tasks
        ]
    }


@router.post("/tasks")
async def create_task(
    body: TaskCreate,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    task = Task(
        user_id=user.id,
        title=body.title,
        category=body.category,
        due=body.due,
        is_urgent=body.is_urgent,
        why=body.why,
        position=body.position,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return {
        "id": str(task.id),
        "title": task.title,
        "category": task.category,
        "due": task.due,
        "is_urgent": task.is_urgent,
        "position": task.position,
        "created_at": task.created_at.isoformat(),
    }


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a task (mark done, reprioritise, etc)."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.title is not None:
        task.title = body.title
    if body.category is not None:
        task.category = body.category
    if body.due is not None:
        task.due = body.due
    if body.is_urgent is not None:
        task.is_urgent = body.is_urgent
    if body.position is not None:
        task.position = body.position
    if body.is_done is not None:
        task.is_done = body.is_done
        task.done_at = datetime.utcnow() if body.is_done else None

    await db.commit()
    await db.refresh(task)
    return {
        "id": str(task.id),
        "title": task.title,
        "category": task.category,
        "is_done": task.is_done,
        "position": task.position,
    }
