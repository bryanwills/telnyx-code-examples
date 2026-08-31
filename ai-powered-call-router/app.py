"""
AI-Powered Call Router

Inbound calls are answered, speech is gathered, intent is classified via the
Telnyx AI Inference API, and the call is transferred to a destination stored in
an in-memory KV route table. Unrecognized intents fall back to a default
queue.
"""

import os
import uuid
from dotenv import load_dotenv
from flask import Flask, jsonify, request

import telnyx

load_dotenv()

app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY")
TELNYX_CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID")

telnyx.api_key = TELNYX_API_KEY

# ---------------------------------------------------------------------------
# KV route table (in-memory). In production, replace with Telnyx KV or Redis.
# Keys are intent labels returned by the LLM; values are transfer destinations.
# ---------------------------------------------------------------------------
ROUTE_TABLE = {
    "billing": "+18005551234",
    "sales": "+18005556789",
    "support": "+18005550000",
}
DEFAULT_DESTINATION = "+18005550000"

# Track call control ids and gathered speech per call.
CALL_STATE = {}


def classify_intent(speech: str) -> str:
    """Classify caller intent using the Telnyx AI Inference API (OpenAI binding)."""
    prompt = (
        "You are an intent classifier for an inbound call router. "
        "Given the caller's spoken request, respond with exactly one of: "
        "billing, sales, support. If unsure, respond: support.\n\n"
        f"Caller said: \"{speech}\"\n\nIntent:"
    )
    try:
        completion = telnyx.ai.openai.chat.create_completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.0,
        )
        intent = completion.choices[0].message.content.strip().lower()
        app.logger.info("Classified intent=%s for speech=%r", intent, speech)
        return intent
    except Exception:
        app.logger.exception("Intent classification failed")
        return "support"


def transfer_call(call_control_id: str, destination: str):
    """Transfer the call to the given destination using Call Control."""
    try:
        telnyx.Call.transfer(
            call_control_id,
            to=destination,
            timeout_secs=30,
        )
        app.logger.info("Transferred call %s to %s", call_control_id, destination)
    except Exception:
        app.logger.exception("Transfer failed for call %s", call_control_id)


def answer_call(call_control_id: str):
    """Answer the inbound call."""
    try:
        telnyx.Call.answer(call_control_id=call_control_id)
        app.logger.info("Answered call %s", call_control_id)
    except Exception:
        app.logger.exception("Answer failed for call %s", call_control_id)


def gather_speech(call_control_id: str):
    """Gather speech from the caller for intent classification."""
    try:
        telnyx.Call.gather_using_speech(
            call_control_id=call_control_id,
            payload={
                "inter_digit_timeout_millis": 2000,
                "timeout_millis": 10000,
                "speech": {
                    "language": "en-US",
                    "end_silence_millis": 1000,
                    "speech_maximum_length": 30,
                },
            },
        )
        app.logger.info("Gather started for call %s", call_control_id)
    except Exception:
        app.logger.exception("Gather failed for call %s", call_control_id)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


@app.route("/webhook", methods=["POST"])
def webhook():
    """Telnyx Call Control webhook handler."""
    raw_body = request.get_data(as_text=True)
    signature = request.headers.get("telnyx-ed25519-signature", "")
    timestamp = request.headers.get("telnyx-ed25519-timestamp", "")

    # Verify webhook signature.
    try:
        event = telnyx.Webhook.unwrap(
            raw_body,
            signature,
            timestamp,
            TELNYX_PUBLIC_KEY,
        )
    except Exception:
        app.logger.exception("Webhook signature verification failed")
        return jsonify(error="invalid signature"), 401

    payload = event.get("data", {}).get("payload", {})
    event_type = event.get("data", {}).get("event_type", "")
    call = payload.get("call", {})
    call_control_id = call.get("call_control_id")

    app.logger.info("Webhook event=%s call=%s", event_type, call_control_id)

    try:
        if event_type == "call.initiated":
            # Inbound call arrived — answer it.
            direction = call.get("direction")
            if direction == "incoming":
                answer_call(call_control_id)
                CALL_STATE[call_control_id] = {"stage": "answered"}

        elif event_type == "call.answered":
            # Play a prompt and gather speech.
            try:
                telnyx.Call.playback_start(
                    call_control_id=call_control_id,
                    payload={
                        "media": [
                            {
                                "type": "text",
                                "text": "Hello, please tell me briefly how I can help you today.",
                            }
                        ]
                    },
                )
            except Exception:
                app.logger.exception("Playback failed for call %s", call_control_id)
            gather_speech(call_control_id)

        elif event_type == "call.gather.ended":
            # Speech gathered — classify intent and transfer.
            speech = payload.get("speech", {}).get("result", "")
            app.logger.info("Gathered speech: %r", speech)
            intent = classify_intent(speech)
            destination = ROUTE_TABLE.get(intent, DEFAULT_DESTINATION)
            transfer_call(call_control_id, destination)

        elif event_type == "call.gather.failed":
            app.logger.warning("Gather failed for call %s, falling back", call_control_id)
            transfer_call(call_control_id, DEFAULT_DESTINATION)

        elif event_type in ("call.hangup", "call.hangup"):
            app.logger.info("Call hung up: %s", call_control_id)
            CALL_STATE.pop(call_control_id, None)

    except Exception:
        app.logger.exception("Unhandled error processing webhook")

    return jsonify(status="ok"), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
