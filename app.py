"""
WhatsApp Real Estate Agent — Flask Application Entry Point

Webhook endpoint that receives WhatsApp messages via Twilio,
passes them through the Claude-powered agent, and replies.
"""

from __future__ import annotations

import logging
import os

from flask import Flask, Response, abort, request
from dotenv import load_dotenv

load_dotenv()

from database import init_db, SessionLocal
from agent import RealEstateAgent
from services import WhatsAppService
from utils import validate_twilio_signature

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Initialise DB tables on startup
init_db()

# Singletons (created once per process)
_agent    = RealEstateAgent()
_whatsapp = WhatsAppService()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health() -> Response:
    return {"status": "ok", "service": "whatsapp-real-estate-agent"}, 200


@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook() -> Response:
    """
    Twilio posts incoming WhatsApp messages here.
    Configure this URL in your Twilio Console →
    Messaging → Senders → WhatsApp → Webhook URL.
    """
    # ── 1. Verify the request came from Twilio ────────────────────────────────
    signature = request.headers.get("X-Twilio-Signature", "")
    url       = request.url
    post_data = request.form.to_dict()

    if not validate_twilio_signature(url, post_data, signature):
        logger.warning("Invalid Twilio signature from %s", request.remote_addr)
        abort(403)

    # ── 2. Extract message details ────────────────────────────────────────────
    sender_phone = _whatsapp.extract_sender(post_data)
    message_body = _whatsapp.extract_body(post_data)

    if not sender_phone or not message_body:
        logger.info("Empty message received — skipping")
        return _empty_twiml()

    logger.info("Incoming | from=%s | body=%r", sender_phone, message_body[:80])

    # ── 3. Run the agent ──────────────────────────────────────────────────────
    db = SessionLocal()
    try:
        reply_text = _agent.reply(
            user_phone   = sender_phone,
            user_message = message_body,
            db           = db,
        )
    except Exception as exc:
        logger.exception("Agent error for %s: %s", sender_phone, exc)
        reply_text = (
            "Sorry, I encountered an error. Please try again in a moment, "
            "or contact us directly at " + os.getenv("AGENCY_PHONE", "our office number.")
        )
    finally:
        db.close()

    # ── 4. Send the reply ─────────────────────────────────────────────────────
    try:
        _whatsapp.send(to=sender_phone, body=reply_text)
    except Exception as exc:
        logger.exception("Failed to send reply to %s: %s", sender_phone, exc)

    # Twilio expects an empty 200 response when you send the reply via the REST API
    return _empty_twiml()


def _empty_twiml() -> Response:
    """Return a minimal TwiML response (Twilio requires valid XML)."""
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        mimetype="text/xml",
    )


# ── Dev server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
