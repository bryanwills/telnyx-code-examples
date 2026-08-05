#!/usr/bin/env python3
"""Multilingual Code-Switching Voice Agent — a Flask app that provisions a
Telnyx AI Assistant configured for real-time language detection and
code-switching, with endpoints to trigger outbound demo calls and a small
browser UI."""

import os
import time
import threading

import requests
import telnyx
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
TELNYX_PHONE_NUMBER = os.getenv("TELNYX_PHONE_NUMBER", "")
TELNYX_CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID", "")
TELNYX_ASSISTANT_ID = os.getenv("TELNYX_ASSISTANT_ID", "")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "multilingual code-switching voice agent")

API = "https://api.telnyx.com/v2"
HEADERS = {
    "Authorization": f"Bearer {TELNYX_API_KEY}",
    "Content-Type": "application/json",
}

_started_at = time.time()


def _start_ttl_cleanup(store, ttl_seconds=3600, interval=300):
    def _cleanup():
        while True:
            time.sleep(interval)
            cutoff = time.time() - ttl_seconds
            expired = [
                k
                for k, v in store.items()
                if isinstance(v, dict) and v.get("_ts", time.time()) < cutoff
            ]
            for k in expired:
                store.pop(k, None)

    threading.Thread(target=_cleanup, daemon=True).start()


calls = {}
_start_ttl_cleanup(calls)


@app.route("/assistant/create", methods=["POST"])
def assistant_create():
    """Create or reuse the multilingual Voice AI Assistant."""
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    client = telnyx.Telnyx(api_key=TELNYX_API_KEY)

    assistant_id = TELNYX_ASSISTANT_ID
    if not assistant_id:
        for a in client.ai.assistants.list():
            if getattr(a, "name", None) == ASSISTANT_NAME:
                assistant_id = a.id
                break

    instructions = """voice: voice ultra katie

you are a friendly multilingual voice agent for a global customer support line.
you can speak english, spanish, portuguese, hindi, and mandarin.

listen carefully to the caller. detect the language they are speaking on every turn.
reply in the same language the caller is using right now.
if the caller switches language mid-conversation or mid-sentence, switch with them.
if you are unsure which language to use, ask in english "which language would you prefer".

keep replies short and natural. this is a phone call.
do not translate unless the caller asks. you are not an interpreter — you are the agent.
if a caller mixes two languages in one sentence, reply in the dominant language.
never say the name of the language out loud unless asked."""

    greeting = (
        "hello, i can speak english, spanish, portuguese, hindi, and mandarin. "
        "please go ahead and speak in any of these languages."
    )

    payload = {
        "name": ASSISTANT_NAME,
        "model": AI_MODEL,
        "instructions": instructions,
        "greeting": greeting,
        "description": (
            "a multilingual voice agent that detects the caller's language on every turn "
            "and replies in the same language, code-switching mid-conversation when the "
            "caller switches."
        ),
        "enabled_features": ["telephony"],
        "transcription": {
            "model": "deepgram/nova-3",
            "language": "multi",
            "settings": {"keyterm": ""},
        },
        "interruption_settings": {
            "enable": True,
            "disable_greeting_interruption": True,
            "interrupt_prediction_threshold": 0.4,
            "start_speaking_plan": {
                "wait_seconds": 0.5,
                "transcription_endpointing_plan": {
                    "on_no_punctuation_seconds": 1.5,
                    "on_punctuation_seconds": 0.4,
                    "on_number_seconds": 1.0,
                },
            },
        },
        "telephony_settings": {
            "noise_suppression": "krisp",
            "user_idle_reply_secs": 10,
            "time_limit_secs": 600,
            "recording_settings": {"enabled": False},
        },
    }

    if TELNYX_CONNECTION_ID:
        payload["telephony_settings"]["default_texml_app_id"] = TELNYX_CONNECTION_ID

    try:
        if assistant_id:
            assistant = client.ai.assistants.update(
                assistant_id=assistant_id, **payload
            )
        else:
            assistant = client.ai.assistants.create(**payload)
    except telnyx.APIStatusError as e:
        return jsonify(
            {"error": f"assistant provisioning failed: {e.status_code} {e.message}"}
        ), e.status_code

    return jsonify(
        {
            "assistant_id": assistant.id,
            "name": assistant.name,
            "model": assistant.model,
            "voice": "voice ultra katie",
            "transcription_model": "deepgram/nova-3",
            "transcription_language": "multi",
            "enabled_features": assistant.enabled_features
            if hasattr(assistant, "enabled_features")
            else ["telephony"],
            "telephony_settings": assistant.telephony_settings
            if hasattr(assistant, "telephony_settings")
            else {},
        }
    ), 200


@app.route("/call/trigger", methods=["POST"])
def call_trigger():
    """Trigger an outbound demo call to a given number."""
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    data = request.get_json(silent=True) or {}
    to_number = data.get("to", "")

    if not to_number:
        return jsonify({"error": "Missing required field: 'to'"}), 400
    if not to_number.startswith("+"):
        return jsonify(
            {"error": "Phone number must be in E.164 format (e.g., +15551234567)"}
        ), 400

    if not TELNYX_PHONE_NUMBER:
        return jsonify({"error": "TELNYX_PHONE_NUMBER is not set"}), 500
    if not TELNYX_CONNECTION_ID:
        return jsonify({"error": "TELNYX_CONNECTION_ID is not set"}), 500

    assistant_id = TELNYX_ASSISTANT_ID
    if not assistant_id:
        return jsonify(
            {
                "error": "TELNYX_ASSISTANT_ID is not set. Run provision_assistant.py first."
            }
        ), 500

    try:
        resp = requests.post(
            f"{API}/texml/ai_calls/{TELNYX_CONNECTION_ID}",
            headers=HEADERS,
            json={
                "From": TELNYX_PHONE_NUMBER,
                "To": to_number,
                "AIAssistantId": assistant_id,
            },
            timeout=30,
        )
        resp.raise_for_status()
    except requests.HTTPError as e:
        return jsonify(
            {"error": f"HTTP {e.response.status_code}: {e.response.text[:300]}"}
        ), e.response.status_code
    except requests.RequestException as e:
        return jsonify({"error": f"network: {str(e)[:200]}"}), 502

    result = resp.json() if resp.content else {}
    call_id = result.get("call_control_id", "")
    calls[call_id] = {
        "to": to_number,
        "from": TELNYX_PHONE_NUMBER,
        "assistant_id": assistant_id,
        "status": "triggered",
    }
    calls[call_id]["_ts"] = time.time()

    return jsonify(
        {
            "call_control_id": call_id,
            "to": to_number,
            "from": TELNYX_PHONE_NUMBER,
            "assistant_id": assistant_id,
            "status": "triggered",
        }
    ), 200


@app.route("/webhooks/call", methods=["POST"])
def handle_call_webhook():
    """Receive Telnyx webhook events. The conversation is handled by the
    Voice AI Assistant — Flask only logs events for observability."""
    if TELNYX_PUBLIC_KEY:
        try:
            client = telnyx.Telnyx(api_key=TELNYX_API_KEY, public_key=TELNYX_PUBLIC_KEY)
            client.webhooks.unwrap(
                request.get_data(as_text=True), headers=dict(request.headers)
            )
        except Exception:
            return jsonify({"error": "invalid signature"}), 401

    payload = request.get_json(silent=True) or {}
    event_type = payload.get("data", {}).get("event_type", "")
    call_control_id = (
        payload.get("data", {}).get("payload", {}).get("call_control_id", "")
    )

    print(f"Webhook: {event_type} for call {call_control_id}")

    return jsonify({"status": "received"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "uptime_s": int(time.time() - _started_at),
            "assistant_configured": bool(TELNYX_ASSISTANT_ID),
            "phone_configured": bool(TELNYX_PHONE_NUMBER),
        }
    ), 200


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multilingual Code-Switching Voice Agent — Telnyx</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #000; --text: #fafafa; --muted: #8a8a8a; --green: #00E3AA; --cream: #F5F0E8;
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif;
    font-size: 17px; line-height: 1.55; margin: 0; min-height: 100vh;
    -webkit-font-smoothing: antialiased; display: flex; align-items: center; justify-content: center; }
  .card { text-align: center; max-width: 500px; padding: 40px; }
  .brand { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 40px; }
  .brand img { height: 32px; }
  .brand .tag { color: var(--muted); font-size: 14px; }
  .brand .tag::before { content: '\\00b7'; margin: 0 10px; }
  h1 { font-size: 32px; font-weight: 700; margin: 0 0 12px; color: var(--cream); }
  .sub { font-size: 16px; color: var(--muted); margin: 0 0 32px; }
  .phone-number { font-size: 28px; font-weight: 700; color: var(--green); margin: 24px 0 8px; }
  .hint { font-size: 14px; color: var(--muted); margin: 0 0 24px; }
  .langs { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 32px; }
  .lang { color: var(--muted); font-size: 14px; }
  .lang:not(:last-child)::after { content: ', '; color: var(--muted); }
  .footer { margin-top: 40px; }
  .footer a { color: var(--green); text-decoration: none; font-size: 14px; }
</style>
</head>
<body>
<div class="card">
  <div class="brand">
    <img src="/telnyx-logo.svg" alt="Telnyx">
    <span class="tag">Voice AI</span>
  </div>
  <h1>Multilingual Code-Switching Agent</h1>
  <p class="sub">Call the number below and speak in any language. Switch mid-conversation and the agent follows you.</p>
  <p class="phone-number">__PHONE_NUMBER__</p>
  <p class="hint">Available now — call from any phone</p>
  <div class="langs">
    <span class="lang">English</span>
    <span class="lang">Spanish</span>
    <span class="lang">Portuguese</span>
    <span class="lang">Hindi</span>
    <span class="lang">Mandarin</span>
  </div>
  <div class="footer">
    <a href="https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-multilingual-code-switching-agent-python" target="_blank">View source &rarr;</a>
  </div>
</div>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return INDEX_HTML.replace(
        "__PHONE_NUMBER__", TELNYX_PHONE_NUMBER or "Not configured"
    )


@app.route("/telnyx-logo.svg", methods=["GET"])
def logo():
    import os as _os

    logo_path = _os.path.join(_os.path.dirname(__file__), "telnyx-logo.svg")
    try:
        from flask import Response

        with open(logo_path, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="image/svg+xml")
    except FileNotFoundError:
        return Response("", status=404)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    host = os.getenv("HOST", "127.0.0.1")
    app.run(debug=False, port=port, host=host)
