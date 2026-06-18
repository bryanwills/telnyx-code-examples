#!/usr/bin/env python3
"""AI Sales Coach (Whisper) — AI listens to a live sales call via conference bridge and whispers real-time coaching to the rep only. The customer never hears the AI."""
import os
import json
import time
import base64
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MAIN_NUMBER = os.getenv("MAIN_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

sessions = {}


def telnyx_post(path, data):
    resp = requests.post(f"{API}{path}", headers=HEADERS, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def telnyx_call_action(call_id, action, data=None):
    return telnyx_post(f"/calls/{call_id}/actions/{action}", data or {})


def call_inference(messages, max_tokens=150):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.6}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


@app.route("/sessions/start", methods=["POST"])
def start_coaching():
    """Start a coached sales call. Dials customer, puts rep + AI in a conference with whisper."""
    data = request.get_json() or {}
    customer_phone = data.get("customer")
    rep_phone = data.get("rep")
    context = data.get("context", "")
    conf_name = f"coach-{int(time.time())}"

    session = {
        "conference": conf_name,
        "customer_phone": customer_phone,
        "rep_phone": rep_phone,
        "context": context,
        "transcript": [],
        "coaching_tips": [],
        "rep_call_id": None,
        "customer_call_id": None,
        "created_at": time.time(),
        "status": "starting",
    }
    sessions[conf_name] = session

    # Dial the rep first
    resp = telnyx_post("/calls", {
        "connection_id": CONNECTION_ID,
        "from": MAIN_NUMBER,
        "to": rep_phone,
        "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
        "client_state": base64.b64encode(json.dumps({
            "conference": conf_name, "role": "rep"
        }).encode()).decode(),
    })
    session["rep_call_id"] = resp.get("data", {}).get("call_control_id", "")

    return jsonify({"session": conf_name, "status": "dialing_rep"}), 201


@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    data = payload.get("data", {})
    event = data.get("event_type", "")
    call_id = data.get("call_control_id", "")
    client_state = {}
    if data.get("client_state"):
        try:
            client_state = json.loads(base64.b64decode(data["client_state"]))
        except Exception:
            pass

    conf_name = client_state.get("conference", "")
    session = sessions.get(conf_name)
    if not session:
        return jsonify({"status": "no_session"}), 200

    role = client_state.get("role", "")

    if event == "call.answered":
        if role == "rep":
            # Rep answered — join them to conference, then dial customer
            telnyx_call_action(call_id, "speak", {
                "payload": "Connecting you now. I'll whisper coaching tips during the call. Only you can hear me.",
                "language": "en-US", "voice": "female",
            })
            session["status"] = "briefing_rep"

        elif role == "customer":
            # Customer answered — join to conference as regular participant
            telnyx_call_action(call_id, "join", {
                "name": conf_name,
                "start_conference_on_create": False,
                "hold": False, "mute": False,
                "supervisor_role": "none",
            })
            session["customer_call_id"] = call_id
            session["status"] = "live"

            # Start media streaming on customer leg for transcript
            try:
                telnyx_call_action(call_id, "streaming_start", {
                    "stream_url": request.url_root.rstrip("/") + "/webhooks/media",
                    "stream_track": "inbound_track",
                })
            except Exception:
                pass

        return jsonify({"status": "answered"}), 200

    if event == "call.speak.ended":
        if session["status"] == "briefing_rep":
            # After briefing, join rep to conference as supervisor (can hear all, speaks to conf)
            telnyx_call_action(call_id, "join", {
                "name": conf_name,
                "start_conference_on_create": True,
                "hold": False, "mute": False,
                "supervisor_role": "barge",
            })

            # Now dial the customer
            resp = telnyx_post("/calls", {
                "connection_id": CONNECTION_ID,
                "from": MAIN_NUMBER,
                "to": session["customer_phone"],
                "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
                "client_state": base64.b64encode(json.dumps({
                    "conference": conf_name, "role": "customer"
                }).encode()).decode(),
            })
            session["customer_call_id"] = resp.get("data", {}).get("call_control_id", "")
            session["status"] = "dialing_customer"
        return jsonify({"status": "spoke"}), 200

    if event == "call.gather.ended":
        speech = data.get("speech", {}).get("result", "")
        if speech and session:
            speaker = "customer" if call_id == session.get("customer_call_id") else "rep"
            session["transcript"].append({"time": time.time(), "speaker": speaker, "text": speech})

            # Generate coaching tip based on what was just said
            if speaker == "customer":
                recent = "\n".join([f"{t['speaker']}: {t['text']}" for t in session["transcript"][-6:]])
                context_info = f"Context: {session.get('context', 'sales call')}" if session.get("context") else ""
                tip = call_inference([
                    {"role": "system", "content": f"You are a sales coach whispering tips to a rep during a live call. Be ultra-concise (1 sentence). Focus on what to say next or how to handle what the customer just said. {context_info}"},
                    {"role": "user", "content": f"Recent conversation:\n{recent}\n\nWhat should the rep do/say next?"},
                ])
                session["coaching_tips"].append({"time": time.time(), "tip": tip, "context": speech})

                # Whisper to rep only (speak on the rep's call leg)
                if session.get("rep_call_id"):
                    try:
                        telnyx_call_action(session["rep_call_id"], "speak", {
                            "payload": tip,
                            "language": "en-US",
                            "voice": "female",
                        })
                    except Exception:
                        pass
        return jsonify({"status": "processed"}), 200

    if event == "call.hangup":
        if call_id == session.get("customer_call_id"):
            session["status"] = "ended"
            # Generate call scorecard
            if session["transcript"]:
                transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in session["transcript"]])
                scorecard = call_inference([
                    {"role": "system", "content": "Score this sales call on: rapport (1-10), discovery questions (1-10), objection handling (1-10), next steps secured (1-10). Give specific feedback on what went well and what to improve. Be direct."},
                    {"role": "user", "content": transcript_text},
                ])
                session["scorecard"] = scorecard
                if SLACK_WEBHOOK:
                    try:
                        requests.post(SLACK_WEBHOOK, json={"text": f"*Sales Call Scorecard: {conf_name}*\n{scorecard}"}, timeout=5)
                    except Exception:
                        pass
        return jsonify({"status": "hangup"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/webhooks/media", methods=["POST"])
def handle_media():
    return jsonify({"status": "received"}), 200


@app.route("/sessions", methods=["GET"])
def list_sessions():
    return jsonify({"sessions": [{
        "name": s["conference"], "status": s["status"],
        "tips_given": len(s["coaching_tips"]),
        "transcript_length": len(s["transcript"]),
    } for s in sessions.values()]}), 200


@app.route("/sessions/<name>", methods=["GET"])
def get_session(name):
    s = sessions.get(name)
    if not s:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "session": s["conference"], "status": s["status"],
        "transcript": s["transcript"],
        "coaching_tips": s["coaching_tips"],
        "scorecard": s.get("scorecard", ""),
    }), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for s in sessions.values() if s["status"] == "live")
    return jsonify({"status": "ok", "active_sessions": active, "total": len(sessions)}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
