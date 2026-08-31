"""
AI-Powered Call Router

Inbound calls are answered, speech is gathered, intent is classified via the
Telnyx AI Inference API, and the call is transferred to a destination stored
in an in-memory KV route table. Unrecognized intents fall back to a default
queue.

Compatible with telnyx>=4.0 (instance-based client API + Ed25519 webhooks).
"""

import logging
import os
import re

from dotenv import load_dotenv
from flask import Flask, jsonify, request

import telnyx
from telnyx.lib.webhooks_ed25519 import unwrap_with_ed25519

load_dotenv()

app = Flask(__name__)
# Force INFO so the request flow is visible (default is WARNING).
app.logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY")
TELNYX_CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID")

# Telnyx-hosted model — no OpenAI BYOK key required.
AI_MODEL = os.getenv("AI_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

client = telnyx.Telnyx(
    api_key=TELNYX_API_KEY,
    public_key=TELNYX_PUBLIC_KEY,
)

# ---------------------------------------------------------------------------
# KV route table (in-memory). In production, replace with Telnyx KV or Redis.
# Keys are intent labels returned by the LLM; values are transfer destinations.
# ---------------------------------------------------------------------------
ROUTE_TABLE = {
    "billing": "+17177247292",
    "sales": "+17177247292",
    "support": "+17177247292",
}
DEFAULT_DESTINATION = "+17177247292"

CALL_STATE = {}


def _g(obj, key, default=None):
    """Attribute-or-item getter for typed SDK models and plain dicts."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def classify_intent(speech: str) -> str:
    """Classify caller intent using the Telnyx AI Inference API."""
    prompt = (
        "You are an intent classifier for an inbound call router. "
        "Read the caller's spoken request and respond with EXACTLY ONE WORD "
        "from this list: billing, sales, support. "
        "Do not include any other text, punctuation, or explanation.\n\n"
        f'Caller said: "{speech}"\n\nIntent:'
    )
    try:
        completion = client.ai.openai.chat.create_completion(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.0,
        )
        # The SDK returns a plain dict for chat completions.
        content = completion["choices"][0]["message"]["content"]
        # Robust extraction: pick the first matching label from the response.
        match = re.search(r"\b(billing|sales|support)\b", content.lower())
        intent = match.group(1) if match else "support"
        app.logger.info("Classified intent=%s (raw=%r) for speech=%r", intent, content, speech)
        return intent
    except Exception:
        app.logger.exception("Intent classification failed")
        return "support"


def transfer_call(call_control_id: str, destination: str):
    """Transfer the call to the given destination using Call Control."""
    try:
        client.calls.actions.transfer(call_control_id, to=destination, timeout_secs=30)
        app.logger.info("Transferred call %s to %s", call_control_id, destination)
    except Exception:
        app.logger.exception("Transfer failed for call %s", call_control_id)


def play_transfer_announcement(call_control_id: str, intent: str):
    """Speak a brief "transferring you to X" message before the transfer fires.

    The actual transfer is deferred until `call.speak.ended` fires for this
    announcement (see the webhook handler) so the TTS isn't cut off by the
    transfer. The pending destination is stashed in CALL_STATE.
    """
    destination = ROUTE_TABLE.get(intent, DEFAULT_DESTINATION)
    message = f"Got it. Transferring you to {intent}. Please hold."
    CALL_STATE[call_control_id] = {
        "stage": "announcing",
        "pending_destination": destination,
        "pending_intent": intent,
    }
    try:
        client.calls.actions.speak(
            call_control_id,
            payload=message,
            voice="female",
            language="en-US",
        )
        app.logger.info("Transfer announcement started for call %s (intent=%s)", call_control_id, intent)
    except Exception:
        app.logger.exception("Transfer announcement failed for call %s", call_control_id)
        # If the announcement can't play, transfer immediately so the caller isn't stranded.
        transfer_call(call_control_id, destination)


def answer_call(call_control_id: str):
    """Answer the inbound call."""
    try:
        client.calls.actions.answer(call_control_id)
        app.logger.info("Answered call %s", call_control_id)
    except Exception:
        app.logger.exception("Answer failed for call %s", call_control_id)


def play_greeting(call_control_id: str):
    """Play the greeting TTS via speak().

    Uses `speak()` (not `gather_using_ai`'s built-in greeting) because
    `speak()` accepts the canonical `voice="female"` alias, while
    `gather_using_ai` uses a different voice set that rejects it.
    The gather starts on `call.speak.ended` (see webhook handler) so the
    greeting finishes before we open the capture window.
    """
    CALL_STATE[call_control_id] = {"stage": "greeting"}
    try:
        client.calls.actions.speak(
            call_control_id,
            payload="Hello, please tell me briefly how I can help you today.",
            voice="female",
            language="en-US",
        )
        app.logger.info("Greeting speak started for call %s", call_control_id)
    except Exception:
        app.logger.exception("Greeting speak failed for call %s", call_control_id)


def start_gather(call_control_id: str):
    """Start speech capture via gather_using_ai.

    `parameters` is a JSON schema describing what to extract — the caller's
    utterance, transcribed verbatim. `assistant` provides the model and a
    one-turn instruction so the LLM just captures, doesn't converse. Telnyx
    fires `call.ai_gather.ended` with the transcript in `payload.result.utterance`.
    No `voice` param is passed — `gather_using_ai` doesn't accept the canonical
    voice aliases that `speak()` does.
    """
    try:
        client.calls.actions.gather_using_ai(
            call_control_id,
            parameters={
                "type": "object",
                "properties": {
                    "utterance": {
                        "type": "string",
                        "description": "The caller's spoken response, transcribed verbatim.",
                    }
                },
                "required": ["utterance"],
            },
            assistant={
                "model": AI_MODEL,
                "instructions": "You are a one-turn speech capture component. Capture exactly what the caller says in the utterance field. Do not ask follow-up questions or give advice.",
            },
            transcription={"language": "en"},
            user_response_timeout_ms=15000,
        )
        app.logger.info("Gather started for call %s", call_control_id)
    except Exception:
        app.logger.exception("Gather failed for call %s", call_control_id)


def extract_user_speech(payload) -> str:
    """Pull the caller's transcribed speech out of an ai_gather.ended payload.

    Prefers `payload.result.utterance` (the schema field we asked for), then
    falls back to the last `role: "user"` entry in `payload.message_history`.
    """
    result = _g(payload, "result")
    if isinstance(result, dict):
        utterance = _g(result, "utterance")
        if utterance:
            return str(utterance).strip()
    history = _g(payload, "message_history") or []
    for msg in reversed(history):
        role = _g(msg, "role")
        if role == "user":
            content = _g(msg, "content", "")
            if content:
                return str(content).strip()
    return ""


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


@app.route("/webhook", methods=["POST"])
def webhook():
    """Telnyx Call Control webhook handler."""
    raw_body = request.get_data(as_text=True)

    # Verify webhook signature (Ed25519) and parse the event.
    try:
        event = unwrap_with_ed25519(
            client,
            raw_body,
            request.headers,
            key=TELNYX_PUBLIC_KEY,
        )
    except Exception:
        app.logger.exception("Webhook signature verification failed")
        return jsonify(error="invalid signature"), 401

    event_data = _g(event, "data")
    event_type = _g(event_data, "event_type", "")
    payload = _g(event_data, "payload")

    # In the current SDK, payload fields (call_control_id, direction, ...)
    # live directly on `payload` — there is no nested `payload.call`.
    call_control_id = _g(payload, "call_control_id")

    app.logger.info("Webhook event=%s call=%s", event_type, call_control_id)

    try:
        if event_type == "call.initiated":
            direction = _g(payload, "direction")
            if direction == "incoming":
                answer_call(call_control_id)
                CALL_STATE[call_control_id] = {"stage": "answered"}
            # Outbound legs (transfer destinations, dials, etc.) are NOT tracked —
            # we only drive the inbound leg through the gather → classify → transfer flow.

        elif event_type == "call.answered":
            # Only play the greeting on the inbound leg we answered (tracked in CALL_STATE).
            # `call.answered` also fires for the transfer destination leg — ignore those.
            if call_control_id in CALL_STATE:
                play_greeting(call_control_id)

        elif event_type == "call.speak.ended":
            # `speak.ended` fires for BOTH the greeting and the transfer announcement.
            # Branch on the stage stored in CALL_STATE.
            if call_control_id in CALL_STATE:
                stage = CALL_STATE[call_control_id].get("stage")
                if stage == "greeting":
                    # Greeting finished — open the speech capture window.
                    start_gather(call_control_id)
                elif stage == "announcing":
                    # Transfer announcement finished — now fire the transfer.
                    destination = CALL_STATE[call_control_id].get("pending_destination", DEFAULT_DESTINATION)
                    intent = CALL_STATE[call_control_id].get("pending_intent", "support")
                    app.logger.info("Announcement done for call %s, transferring to %s (%s)", call_control_id, destination, intent)
                    transfer_call(call_control_id, destination)

        elif event_type == "call.ai_gather.ended":
            if call_control_id in CALL_STATE:
                speech = extract_user_speech(payload)
                app.logger.info("Gathered speech: %r", speech)
                intent = classify_intent(speech)
                play_transfer_announcement(call_control_id, intent)

        elif event_type == "call.ai_gather.failed":
            if call_control_id in CALL_STATE:
                app.logger.warning("AI gather failed for call %s, falling back", call_control_id)
                play_transfer_announcement(call_control_id, "support")

        elif event_type == "call.hangup":
            app.logger.info("Call hung up: %s", call_control_id)
            CALL_STATE.pop(call_control_id, None)

    except Exception:
        app.logger.exception("Unhandled error processing webhook")

    return jsonify(status="ok"), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
