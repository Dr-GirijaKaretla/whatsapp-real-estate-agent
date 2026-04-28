"""Security utilities — Twilio request signature verification."""

from __future__ import annotations

import os

from twilio.request_validator import RequestValidator


def validate_twilio_signature(url: str, post_data: dict, signature: str) -> bool:
    """
    Verify that the incoming webhook request genuinely came from Twilio.
    Returns True if valid, False otherwise.
    Set SKIP_TWILIO_VALIDATION=true to bypass during local development.
    """
    if os.getenv("SKIP_TWILIO_VALIDATION", "false").lower() == "true":
        return True

    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    validator = RequestValidator(auth_token)
    return validator.validate(url, post_data, signature)
