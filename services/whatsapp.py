"""Twilio WhatsApp send/receive service — lazy-initialized."""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)

_PREFIX = "whatsapp:"


class WhatsAppService:
    def __init__(self) -> None:
        self._client      = None
        self._from_number = None

    def _ensure_client(self) -> None:
        """Create the Twilio client on first use so missing creds don't crash startup."""
        if self._client is not None:
            return
        from twilio.rest import Client
        sid    = os.environ.get("TWILIO_ACCOUNT_SID", "")
        token  = os.environ.get("TWILIO_AUTH_TOKEN", "")
        number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")
        if not sid or not token or not number:
            raise RuntimeError(
                "Twilio credentials not set. Add TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER to your environment variables."
            )
        self._client      = Client(sid, token)
        self._from_number = _PREFIX + number

    def send(self, to: str, body: str) -> str:
        self._ensure_client()
        chunks   = self._split(body, max_len=3000)
        last_sid = ""
        for chunk in chunks:
            msg = self._client.messages.create(
                from_=self._from_number,
                to=_PREFIX + to,
                body=chunk,
            )
            last_sid = msg.sid
            logger.debug("Sent SID=%s to=%s", msg.sid, to)
        return last_sid

    @staticmethod
    def _split(text: str, max_len: int = 3000) -> list[str]:
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
        return form_data.get("From", "").replace(_PREFIX, "").strip()

    @staticmethod
    def extract_body(form_data: dict) -> str:
        return form_data.get("Body", "").strip()
