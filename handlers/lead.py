"""Lead capture and management."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from database.models import Lead, LeadStatus


class LeadHandler:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, phone: str) -> Lead:
        """Return existing lead or create a new one."""
        lead = self.db.query(Lead).filter(Lead.phone == phone).first()
        if not lead:
            lead = Lead(phone=phone)
            self.db.add(lead)
            self.db.commit()
            self.db.refresh(lead)
        else:
            lead.last_seen = datetime.utcnow()
            self.db.commit()
        return lead

    def save(self, lead_phone: str, **kwargs: Any) -> str:
        """Upsert lead data from agent-collected fields."""
        lead = self.get_or_create(lead_phone)

        updatable = {
            "name", "email", "intent", "preferred_type", "preferred_city",
            "preferred_area", "min_budget", "max_budget", "min_bedrooms", "notes",
        }
        for k, v in kwargs.items():
            if k in updatable and v is not None:
                setattr(lead, k, v)

        # Auto-advance status
        if lead.status == LeadStatus.new and lead.name:
            lead.status = LeadStatus.contacted

        self.db.commit()
        return f"✅ Lead info saved for {lead.name or lead.phone}."

    def update_status(self, lead_id: int, status: str) -> str:
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return f"Lead #{lead_id} not found."
        lead.status = status
        self.db.commit()
        return f"✅ Lead #{lead_id} status updated to {status}."

    def summary(self, status_filter: str = "all") -> str:
        q = self.db.query(Lead)
        if status_filter != "all":
            q = q.filter(Lead.status == status_filter)

        leads = q.order_by(Lead.created_at.desc()).all()
        if not leads:
            return "No leads found."

        lines = [f"*Leads Report* ({len(leads)} total)\n"]
        for lead in leads:
            budget = ""
            if lead.max_budget:
                budget = f"  💰 Budget: ${lead.max_budget:,.0f}"
            lines.append(
                f"• *{lead.name or 'Unknown'}* ({lead.phone})\n"
                f"  Status: {lead.status}  |  Intent: {lead.intent or '?'}{budget}"
            )
        return "\n".join(lines)
