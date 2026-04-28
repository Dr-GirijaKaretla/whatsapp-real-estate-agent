"""
WhatsApp Real Estate Agent — Flask Application Entry Point

Webhook endpoint that receives WhatsApp messages via Twilio,
passes them through the Claude-powered agent, and replies.

Key design: webhook returns 200 to Twilio IMMEDIATELY (within 1s),
then processes the message in a background thread to avoid Twilio's
15-second timeout and the retry storm it causes.
"""

from __future__ import annotations

import logging
import os
import threading

from flask import Flask, Response, abort, request
from dotenv import load_dotenv

load_dotenv()

from database import init_db, SessionLocal
from agent import RealEstateAgent
from services import WhatsAppService
from services.rate_limiter import PerUserQueue
from utils import validate_twilio_signature

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

init_db()

_agent    = RealEstateAgent()
_whatsapp = WhatsAppService()

# Per-user queue — each user's messages are processed in order,
# but different users are processed in parallel
_MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))
_queue       = PerUserQueue(max_workers=_MAX_WORKERS)

# Deduplication: ignore Twilio retries for messages already being processed
_in_flight: set[str] = set()
_in_flight_lock = threading.Lock()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health() -> Response:
    return {"status": "ok", "service": "whatsapp-real-estate-agent", "workers": _MAX_WORKERS}, 200


@app.route("/seed", methods=["GET"])
def seed() -> Response:
    """Load sample properties into the database. Visit once after deployment."""
    from seed import seed_database
    result = seed_database()
    return {"message": result}, 200


@app.route("/properties", methods=["GET"])
def list_properties() -> Response:
    """Quick view of all active properties — for verification only."""
    db = SessionLocal()
    try:
        from database.models import Property
        props = db.query(Property).filter(Property.is_active == True).all()
        return {
            "count": len(props),
            "properties": [p.to_dict() for p in props]
        }, 200
    finally:
        db.close()


@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook() -> Response:
    """
    Twilio posts incoming WhatsApp messages here.
    Returns 200 immediately; processes the message in the background.
    """
    # ── 1. Verify the request came from Twilio ────────────────────────────────
    signature = request.headers.get("X-Twilio-Signature", "")
    post_data = request.form.to_dict()

    if not validate_twilio_signature(request.url, post_data, signature):
        logger.warning("Invalid Twilio signature from %s", request.remote_addr)
        abort(403)

    # ── 2. Extract message details ────────────────────────────────────────────
    sender_phone = _whatsapp.extract_sender(post_data)
    message_body = _whatsapp.extract_body(post_data)
    message_sid  = post_data.get("MessageSid", "")

    if not sender_phone or not message_body:
        return _empty_twiml()

    # ── 3. Deduplicate Twilio retries ─────────────────────────────────────────
    with _in_flight_lock:
        if message_sid and message_sid in _in_flight:
            logger.info("Duplicate SID %s — skipping", message_sid)
            return _empty_twiml()
        if message_sid:
            _in_flight.add(message_sid)

    logger.info("Queued | from=%s | sid=%s | body=%r", sender_phone, message_sid, message_body[:80])

    # ── 4. Return 200 to Twilio immediately, process in background ────────────
    _queue.submit(sender_phone, _process_message, sender_phone, message_body, message_sid)
    return _empty_twiml()


def _process_message(sender_phone: str, message_body: str, message_sid: str) -> None:
    """Run the agent and send the reply. Executed in a worker thread."""
    try:
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
                "Sorry, I ran into a problem. Please try again in a moment, "
                "or call us at " + os.getenv("AGENCY_PHONE", "our office.")
            )
        finally:
            db.close()

        _whatsapp.send(to=sender_phone, body=reply_text)

    except Exception as exc:
        logger.exception("Unhandled error processing message from %s: %s", sender_phone, exc)
    finally:
        with _in_flight_lock:
            _in_flight.discard(message_sid)


def _empty_twiml() -> Response:
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        mimetype="text/xml",
    )


# ── Dev server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
