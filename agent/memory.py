"""Manage per-lead conversation history stored in the database."""

from __future__ import annotations

from sqlalchemy.orm import Session
from database.models import Conversation

MAX_HISTORY = 20   # messages kept per lead


def get_history(db: Session, lead_id: int) -> list[dict]:
    """Return the last MAX_HISTORY messages for a lead as Claude-format dicts."""
    rows = (
        db.query(Conversation)
        .filter(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at.asc())
        .all()
    )
    # Keep only the most recent window
    rows = rows[-MAX_HISTORY:]
    return [{"role": row.role, "content": row.content} for row in rows]


def save_message(db: Session, lead_id: int, role: str, content: str) -> None:
    """Persist a single message and trim history beyond MAX_HISTORY."""
    db.add(Conversation(lead_id=lead_id, role=role, content=content))
    db.commit()

    # Trim old messages
    total = db.query(Conversation).filter(Conversation.lead_id == lead_id).count()
    if total > MAX_HISTORY:
        oldest = (
            db.query(Conversation)
            .filter(Conversation.lead_id == lead_id)
            .order_by(Conversation.created_at.asc())
            .limit(total - MAX_HISTORY)
            .all()
        )
        for row in oldest:
            db.delete(row)
        db.commit()
