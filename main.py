"""
n0x - Instagram DM auto-reply system (Flask demo entrypoint)

Lightweight Flask app that demonstrates receiving messages, storing them,
updating style profiles, and sending adaptive replies without using external
AI models. Designed to be deployable on PythonAnywhere.

Endpoints:
- POST /receive_message: receive a message from another user
- POST /ingest_owner_message: ingest an owner message to learn style

This file orchestrates the modules in this project.
"""
from flask import Flask, request, jsonify
import time
import random
import os

from memory_manager import MemoryManager
from intent_engine import IntentEngine
from style_engine import StyleEngine
from response_engine import ResponseEngine
from personality_engine import PersonalityEngine

app = Flask(__name__)

# Ensure data dir exists in working folder
os.makedirs("data/conversations", exist_ok=True)
os.makedirs("data/profiles", exist_ok=True)

# Initialize components
memory = MemoryManager(data_dir="data")
intent = IntentEngine()
style = StyleEngine(memory)
personality = PersonalityEngine()
responder = ResponseEngine(memory, style, personality)


def simulate_typing_delay(message_text):
    """Typing delay scales with message length for human-like pacing."""
    base = max(0.3, min(3.0, len(message_text) / 80.0))
    jitter = random.uniform(0.0, 0.6)
    time.sleep(base + jitter)


@app.route("/receive_message", methods=["POST"])
def receive_message():
    """API endpoint to receive incoming messages.
    Expected JSON: {"user_id": str, "from_id": str, "text": str}
    """
    data = request.get_json(force=True)
    reply, status = _process_incoming_payload(data)
    return jsonify(reply), status


@app.route('/webhook', methods=['POST'])
def webhook():
    """Compatibility endpoint for platforms expecting /webhook.
    Forwards payload to same processor as `/receive_message`.
    """
    data = request.get_json(force=True)
    reply, status = _process_incoming_payload(data)
    return jsonify(reply), status


def _process_incoming_payload(data: dict):
    """Process an incoming message payload and return (response_obj, status_code).
    Expected keys: user_id, from_id, text
    """
    user_id = data.get("user_id")
    from_id = data.get("from_id")
    text = (data.get("text") or "").strip()
    if not user_id or not from_id or text == "":
        return {"error": "Missing fields"}, 400

    # Save incoming message
    memory.save_message(user_id, from_id, text, sender="other")

    # Anti-spam: repeated identical messages
    if memory.is_repeated_message(user_id, from_id, text):
        reply = responder.handle_spam(user_id, from_id)
        simulate_typing_delay(reply)
        memory.save_message(user_id, from_id, reply, sender="owner")
        return {"reply": reply}, 200

    # Intent detection (rule-based)
    detected = intent.detect(text)

    # WhatsApp request handling: track requests and NEVER auto-send number
    if detected == "asking_for_whatsapp":
        cnt = memory.increment_whatsapp_requests(user_id, from_id)
        reply = responder.handle_whatsapp_request(user_id, from_id, cnt)
        simulate_typing_delay(reply)
        memory.save_message(user_id, from_id, reply, sender="owner")
        return {"reply": reply}, 200

    # Possibly recalc style if thresholds met
    style.maybe_recalculate(user_id)

    # Generate reply
    reply = responder.generate_reply(user_id, from_id, text, detected)

    # Simulate typing and mark seen
    simulate_typing_delay(reply)
    memory.mark_seen(user_id, from_id)

    # Save owner's outgoing message
    memory.save_message(user_id, from_id, reply, sender="owner")

    return {"reply": reply}, 200


@app.route("/ingest_owner_message", methods=["POST"])
def ingest_owner_message():
    """Endpoint for ingesting owner-written messages to learn style.
    JSON: {"user_id": str, "to_id": str, "text": str}
    """
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    to_id = data.get("to_id")
    text = (data.get("text") or "").strip()
    if not user_id or not to_id or text == "":
        return jsonify({"error": "Missing fields"}), 400

    memory.save_message(user_id, to_id, text, sender="owner")
    # Recalculate immediately if threshold reached
    style.maybe_recalculate(user_id)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # For local testing only; on PythonAnywhere the WSGI config should import `app`
    app.run(host="0.0.0.0", port=5000, debug=True)
