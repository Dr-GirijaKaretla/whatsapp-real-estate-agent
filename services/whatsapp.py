"""Twilio WhatsApp send/receive service."""

from __future__ import annotations

import os
import logging

from twilio.rest import Client

logger = logging.getLogger(__name__)

# WhatsApp numbers must be prefixed with "whatsapp:"
_PREFIX = "whatsapp:"


class WhatsAppService:
    def __init__(self) -> None:
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token  = os.environ["TWILIO_AUTH_TOKEN"]
        self.from_number = _PREFIX + os.environ["TWILIO_WHATSAPP_NUMBER"]
        self.client = Client(account_sid, auth_token)

    def send(self, to: str, body: str) -> str:
        """
        Send a WhatsApp message.

        Args:
            to:   Recipient E.164 number (without whatsapp: prefix).
            body: Message text (markdown-style *bold* works on WhatsApp).

        Returns:
            Twilio message SID.
        """
        # Split long messages (WhatsApp cap ~4096 chars but we stay safe)
        chunks = self._split(body, max_len=3000)
        last_sid = ""
        for chunk in chunks:
            msg = self.client.messages.create(
                from_=self.from_number,
                to=_PREFIX + to,
                body=chunk,
            )
            last_sid = msg.sid
            logger.debug("Sent message SID=%s to=%s", msg.sid, to)
        return last_sid

    @staticmethod
    def _split(text: str, max_len: int = 3000) -> list[str]:
        """Split text into chunks without cutting mid-word."""
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")
        return chunks

    @staticmethod
    def extract_sender(form_data: dict) -> str:
        """Extract clean E.164 number from Twilio's 'From' field."""
        raw = form_data.get("From", "")
        return raw.replace(_PREFIX, "").strip()

    @staticmethod
    def extract_body(form_data: dict) -> str:
        return form_data.get("Body", "").strip()
