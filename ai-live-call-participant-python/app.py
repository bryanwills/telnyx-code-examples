#!/usr/bin/env python3
"""AI Live Call Participant — AI joins a multi-human conference call as an active participant. Listens via media streaming, contributes via TTS, takes real-time notes, and responds when addressed by name."""
import os
import json
import time
import base64
import struct
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MAIN_NUMBER = os.getenv("MAIN_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
AI_NAME = os.getenv("AI_NAME", "Alex")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

# Active conferences with AI participant
conferences = {}

# Per-call state
calls = {}


def telnyx_post(path, data):
    resp = requests.post(f"{API}{path}", headers=HEADERS, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def telnyx_call_action(call_id, action, data=None):
    return telnyx_post(f"/calls/{call_id}/actions/{action}", data or {})


def call_inference(messages, max_tokens=200):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.7}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def post_slack(text):
    if SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=5)
        except Exception:
            pass


@app.route("/conferences/create", methods=["POST"])
def create_conference():
    """Create a conference and have AI join as a participant."""
    data = request.get_json() or {}
    conf_name = data.get("name", f"ai-conf-{int(time.time())}")
    participants = data.get("participants", [])

    conf = {
        "name": conf_name,
        "created_at": time.time(),
        "participants": {},
        "transcript": [],
        "ai_joined": False,
        "notes": [],
    }
    conferences[conf_name] = conf

    # Dial out to each human participant
    for phone in participants:
        resp = telnyx_post("/calls", {
            "connection_id": CONNECTION_ID,
            "from": MAIN_NUMBER,
            "to": phone,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
            "client_state": base64.b64encode(json.dumps({
                "conference": conf_name, "role": "human"
            }).encode()).decode(),
        })
        call_id = resp.get("data", {}).get("call_control_id", "")
        conf["participants"][call_id] = {"phone": phone, "role": "human", "status": "dialing"}

    return jsonify({"conference": conf_name, "participants": len(participants)}), 201


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
    conf = conferences.get(conf_name)

    if event == "call.initiated" and data.get("direction") == "incoming":
        telnyx_call_action(call_id, "answer")
        return jsonify({"status": "answering"}), 200

    if event == "call.answered":
        if conf:
            # Join this caller to the conference
            telnyx_call_action(call_id, "join", {
                "name": conf_name,
                "start_conference_on_create": True,
                "hold": False,
                "mute": False,
                "supervisor_role": "none",
            })
            if call_id in conf["participants"]:
                conf["participants"][call_id]["status"] = "joined"

            # Start media streaming to capture audio for AI analysis
            try:
                telnyx_call_action(call_id, "streaming_start", {
                    "stream_url": request.url_root.rstrip("/") + "/webhooks/media",
                    "stream_track": "both_tracks",
                    "client_state": base64.b64encode(json.dumps({
                        "conference": conf_name, "call_id": call_id
                    }).encode()).decode(),
                })
            except Exception:
                pass

            # If AI hasn't joined yet, announce and enable AI
            if not conf.get("ai_joined"):
                conf["ai_joined"] = True
                telnyx_call_action(call_id, "speak", {
                    "payload": f"Hi everyone, this is {AI_NAME}, your AI assistant for this call. I'll be listening and taking notes. Say my name if you need me to weigh in.",
                    "language": "en-US",
                    "voice": "female",
                })
        return jsonify({"status": "answered"}), 200

    if event == "call.speak.ended":
        # After AI speaks, start gathering to listen for its name
        if conf:
            try:
                telnyx_call_action(call_id, "gather_using_speak", {
                    "payload": " ",
                    "language": "en-US",
                    "voice": "female",
                    "minimum_digits": 1,
                    "maximum_digits": 1,
                    "inter_digit_timeout": 30,
                    "valid_digits": "0123456789*#",
                    "client_state": base64.b64encode(json.dumps({
                        "conference": conf_name, "listening": True
                    }).encode()).decode(),
                })
            except Exception:
                pass
        return jsonify({"status": "listening"}), 200

    if event == "call.gather.ended":
        # Process any speech that came through
        speech = data.get("speech", {}).get("result", "")
        if speech and conf:
            conf["transcript"].append({
                "time": time.time(),
                "speaker": "participant",
                "text": speech,
            })

            # Check if AI was addressed
            if AI_NAME.lower() in speech.lower():
                # AI should respond
                context = "\n".join([f"{t['speaker']}: {t['text']}" for t in conf["transcript"][-10:]])
                prompt = f"You are {AI_NAME}, an AI participant in a live phone conference. You were just addressed. Recent conversation:\n{context}\n\nRespond helpfully and concisely (2-3 sentences max). You're a real participant, not a bot reading a script."
                response = call_inference([
                    {"role": "system", "content": f"You are {AI_NAME}, an AI conference call participant. Be natural, concise, helpful."},
                    {"role": "user", "content": prompt},
                ])
                conf["transcript"].append({
                    "time": time.time(),
                    "speaker": AI_NAME,
                    "text": response,
                })
                telnyx_call_action(call_id, "speak", {
                    "payload": response,
                    "language": "en-US",
                    "voice": "female",
                })
        return jsonify({"status": "processed"}), 200

    if event == "call.hangup":
        if conf and call_id in conf.get("participants", {}):
            conf["participants"][call_id]["status"] = "left"

            # If all humans left, generate summary
            active = [p for p in conf["participants"].values() if p["status"] == "joined" and p["role"] == "human"]
            if not active and conf["transcript"]:
                transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in conf["transcript"]])
                summary = call_inference([
                    {"role": "system", "content": "Summarize this conference call. Include: key decisions, action items with owners, and unresolved questions. Be structured and concise."},
                    {"role": "user", "content": transcript_text},
                ])
                conf["notes"] = summary
                post_slack(f"*Call Summary: {conf_name}*\n{summary}")
        return jsonify({"status": "hangup"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/webhooks/media", methods=["POST"])
def handle_media():
    """Receive media streaming chunks for real-time audio analysis."""
    payload = request.get_json()
    # In production: buffer PCM audio, run VAD, transcribe chunks,
    # detect when AI is addressed, trigger response
    return jsonify({"status": "received"}), 200


@app.route("/conferences", methods=["GET"])
def list_conferences():
    return jsonify({
        "conferences": [{
            "name": c["name"],
            "participants": len(c["participants"]),
            "ai_joined": c["ai_joined"],
            "transcript_length": len(c["transcript"]),
        } for c in conferences.values()]
    }), 200


@app.route("/conferences/<name>/transcript", methods=["GET"])
def get_transcript(name):
    conf = conferences.get(name)
    if not conf:
        return jsonify({"error": "not found"}), 404
    return jsonify({"conference": name, "transcript": conf["transcript"], "notes": conf.get("notes", [])}), 200


@app.route("/conferences/<name>/ask", methods=["POST"])
def ask_ai(name):
    """Ask the AI a question about an ongoing or completed conference."""
    conf = conferences.get(name)
    if not conf:
        return jsonify({"error": "not found"}), 404
    data = request.get_json() or {}
    question = data.get("question", "")
    transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in conf["transcript"]])
    answer = call_inference([
        {"role": "system", "content": "You are an AI that participated in this conference call. Answer questions about what was discussed."},
        {"role": "user", "content": f"Transcript:\n{transcript_text}\n\nQuestion: {question}"},
    ])
    return jsonify({"answer": answer}), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for c in conferences.values() if c.get("ai_joined") and
                 any(p["status"] == "joined" for p in c["participants"].values()))
    return jsonify({"status": "ok", "active_conferences": active, "total": len(conferences)}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
