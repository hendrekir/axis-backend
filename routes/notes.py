"""
Notes routes — save, list, and search smart notes.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Note, User
from routes.auth import get_authenticated_user
from services.notes_service import save_note, search_notes, get_related_notes

router = APIRouter(tags=["Notes"])


class NoteCreate(BaseModel):
    content: str
    source: str = "manual"
    context: dict = {}


@router.post("/notes")
async def create_note(
    body: NoteCreate,
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a new note."""
    note = await save_note(
        user_id=user.id,
        content=body.content,
        source=body.source,
        context=body.context,
        db=db,
    )
    await db.commit()
    return {
        "id": str(note.id),
        "content": note.content,
        "tags": note.tags,
        "source": note.source,
        "created_at": note.created_at.isoformat() if note.created_at else None,
    }


@router.get("/notes")
async def list_notes(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """List recent notes."""
    result = await db.execute(
        select(Note)
        .where(Note.user_id == user.id)
        .order_by(Note.created_at.desc())
        .limit(limit)
    )
    notes = result.scalars().all()
    return {
        "notes": [
            {
                "id": str(n.id),
                "content": n.content,
                "tags": n.tags or [],
                "source": n.source,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ]
    }


@router.get("/notes/search")
async def search(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search across notes, with related tasks and thread mentions."""
    related = await get_related_notes(user.id, q, db)
    return related
