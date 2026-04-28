"""
Core Claude-powered Real Estate Agent.

Handles a full agentic loop:
  1. Build message history
  2. Call Claude with tools
  3. Execute any tool calls
  4. Continue until Claude returns a final text reply
"""

from __future__ import annotations

import os
import logging
from typing import Any

import anthropic
from sqlalchemy.orm import Session

from .prompts import SYSTEM_PROMPT, ADMIN_CONTEXT
from .tools import TOOLS
from .memory import get_history, save_message

logger = logging.getLogger(__name__)

# Admins are identified by phone number stored in ADMIN_PHONES env var
# comma-separated, e.g.  ADMIN_PHONES="+1234567890,+0987654321"
_ADMIN_PHONES: set[str] = set(
    p.strip() for p in os.getenv("ADMIN_PHONES", "").split(",") if p.strip()
)


class RealEstateAgent:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

        # Import handlers lazily to avoid circular imports at module load time
        from handlers.property import PropertyHandler
        from handlers.lead import LeadHandler
        from handlers.appointment import AppointmentHandler
        from handlers.faq import FAQHandler

        self._property_handler    = PropertyHandler
        self._lead_handler        = LeadHandler
        self._appointment_handler = AppointmentHandler
        self._faq_handler         = FAQHandler

    # ── Public API ────────────────────────────────────────────────────────────

    def reply(self, user_phone: str, user_message: str, db: Session) -> str:
        """
        Process a WhatsApp message and return the agent's reply.

        Args:
            user_phone:   Sender's E.164 phone number (e.g. +12125551234).
            user_message: The text the user sent.
            db:           SQLAlchemy session.

        Returns:
            The text response to send back via WhatsApp.
        """
        is_admin = user_phone in _ADMIN_PHONES

        # Ensure lead record exists
        lead = LeadHandler(db).get_or_create(phone=user_phone)

        # Persist the incoming message
        save_message(db, lead.id, "user", user_message)

        # Build history
        history = get_history(db, lead.id)

        # Build system prompt
        system = SYSTEM_PROMPT
        if is_admin:
            system += ADMIN_CONTEXT

        # Agentic loop
        response_text = self._run_loop(system, history, db, lead, is_admin)

        # Persist the reply
        save_message(db, lead.id, "assistant", response_text)

        return response_text

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run_loop(
        self,
        system: str,
        messages: list[dict],
        db: Session,
        lead: Any,
        is_admin: bool,
    ) -> str:
        """Run the agentic tool-use loop until a final text reply is produced."""
        current_messages = list(messages)

        for _ in range(10):   # safety cap — max 10 tool rounds
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system,
                tools=TOOLS,
                messages=current_messages,
            )

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                # Append assistant's response (may contain text + tool_use blocks)
                assistant_content = [block.model_dump() for block in response.content]
                current_messages.append({"role": "assistant", "content": assistant_content})

                # Execute each tool call and build tool_result blocks
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._dispatch_tool(
                            block.name, block.input, db, lead, is_admin
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

                current_messages.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason
            break

        return "I'm sorry, I ran into a problem. Please try again."

    def _dispatch_tool(
        self,
        name: str,
        inputs: dict,
        db: Session,
        lead: Any,
        is_admin: bool,
    ) -> Any:
        """Route a tool call to the appropriate handler."""
        logger.info("Tool call: %s | inputs: %s", name, inputs)

        ph = self._property_handler(db)
        lh = self._lead_handler(db)
        ah = self._appointment_handler(db)
        fh = self._faq_handler(db)

        if name == "search_properties":
            return ph.search(**inputs)

        if name == "get_property_details":
            return ph.get_details(inputs["property_id"])

        if name == "book_appointment":
            return ah.book(
                property_id  = inputs["property_id"],
                client_name  = inputs["client_name"],
                client_phone = inputs["client_phone"],
                scheduled_at = inputs["scheduled_at"],
                notes        = inputs.get("notes"),
            )

        if name == "save_lead":
            return lh.save(lead_phone=lead.phone, **inputs)

        if name == "answer_faq":
            return fh.answer(inputs["question"])

        if name == "escalate_to_human":
            return self._escalate(inputs, lead)

        # Admin-only tools
        if not is_admin:
            return "❌ You don't have permission to use this command."

        if name == "get_appointments":
            return ah.list_appointments(inputs.get("date_filter", "today"))

        if name == "get_leads_summary":
            return lh.summary(inputs.get("status_filter", "all"))

        if name == "add_property":
            return ph.add(**inputs)

        return f"Unknown tool: {name}"

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Pull the first text block out of a Claude response."""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    @staticmethod
    def _escalate(inputs: dict, lead: Any) -> str:
        """Log escalation request (hook in your notification system here)."""
        logger.warning(
            "ESCALATION requested | phone=%s name=%s reason=%s",
            inputs.get("client_phone"),
            inputs.get("client_name"),
            inputs.get("reason"),
        )
        return (
            "Escalation logged. A human agent will contact "
            f"{inputs.get('client_name', 'the client')} shortly."
        )
