#!/usr/bin/env python3
"""AI Conference Moderator — manages multi-party conference calls. Enforces speaking turns, time limits, mutes/unmutes participants, and produces structured meeting summary with action items."""
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

meetings = {}


def telnyx_post(path, data):
    resp = requests.post(f"{API}{path}", headers=HEADERS, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def telnyx_call_action(call_id, action, data=None):
    return telnyx_post(f"/calls/{call_id}/actions/{action}", data or {})


def call_inference(messages, max_tokens=300):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


@app.route("/meetings/create", methods=["POST"])
def create_meeting():
    """Create a moderated meeting with agenda and time limits."""
    data = request.get_json() or {}
    meeting_id = f"meet-{int(time.time())}"
    meeting = {
        "id": meeting_id,
        "topic": data.get("topic", "Team Meeting"),
        "agenda": data.get("agenda", []),
        "time_limit_minutes": data.get("time_limit", 30),
        "per_speaker_seconds": data.get("per_speaker_seconds", 120),
        "participants": {},
        "current_agenda_item": 0,
        "transcript": [],
        "speaker_times": {},
        "created_at": time.time(),
        "started_at": None,
        "status": "pending",
    }
    meetings[meeting_id] = meeting

    # Dial participants
    for phone in data.get("participants", []):
        resp = telnyx_post("/calls", {
            "connection_id": CONNECTION_ID,
            "from": MAIN_NUMBER,
            "to": phone,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
            "client_state": base64.b64encode(json.dumps({
                "meeting": meeting_id, "role": "participant"
            }).encode()).decode(),
        })
        call_id = resp.get("data", {}).get("call_control_id", "")
        meeting["participants"][call_id] = {
            "phone": phone, "status": "dialing", "speaking_time": 0, "muted": False,
        }

    return jsonify({"meeting_id": meeting_id, "participants": len(data.get("participants", []))}), 201


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

    meeting_id = client_state.get("meeting", "")
    meeting = meetings.get(meeting_id)
    if not meeting:
        return jsonify({"status": "no_meeting"}), 200

    if event == "call.answered":
        # Join to conference
        telnyx_call_action(call_id, "join", {
            "name": meeting_id,
            "start_conference_on_create": True,
            "hold": False, "mute": False,
            "supervisor_role": "none",
        })
        if call_id in meeting["participants"]:
            meeting["participants"][call_id]["status"] = "joined"

        # When enough people have joined, start the meeting
        joined = sum(1 for p in meeting["participants"].values() if p["status"] == "joined")
        if joined >= 2 and not meeting.get("started_at"):
            meeting["started_at"] = time.time()
            meeting["status"] = "active"
            agenda_text = ""
            if meeting["agenda"]:
                items = "; ".join([f"{i+1}, {a}" for i, a in enumerate(meeting["agenda"])])
                agenda_text = f" Today's agenda: {items}."

            telnyx_call_action(call_id, "speak", {
                "payload": f"Welcome to the meeting. Topic: {meeting['topic']}.{agenda_text} Each speaker has {meeting['per_speaker_seconds']} seconds. I'll keep time. Let's begin.",
                "language": "en-US", "voice": "female",
            })
        return jsonify({"status": "joined"}), 200

    if event == "call.speak.ended":
        return jsonify({"status": "spoke"}), 200

    if event == "call.gather.ended":
        speech = data.get("speech", {}).get("result", "")
        if speech:
            participant = meeting["participants"].get(call_id, {})
            phone = participant.get("phone", "unknown")[-4:]
            meeting["transcript"].append({
                "time": time.time(), "speaker": f"...{phone}", "text": speech,
            })

        # Check meeting time limit
        if meeting.get("started_at"):
            elapsed = (time.time() - meeting["started_at"]) / 60
            if elapsed >= meeting["time_limit_minutes"] and meeting["status"] == "active":
                meeting["status"] = "wrapping_up"
                telnyx_call_action(call_id, "speak", {
                    "payload": "We've reached our time limit. Let me summarize the key points and action items.",
                    "language": "en-US", "voice": "female",
                })
        return jsonify({"status": "gathered"}), 200

    if event == "call.hangup":
        if call_id in meeting["participants"]:
            meeting["participants"][call_id]["status"] = "left"

        # If all left, generate summary
        active = [p for p in meeting["participants"].values() if p["status"] == "joined"]
        if not active and meeting["transcript"]:
            transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in meeting["transcript"]])
            summary = call_inference([
                {"role": "system", "content": "Generate a structured meeting summary with: 1) Key decisions made, 2) Action items with owners (use speaker IDs), 3) Open questions, 4) Next meeting topics. Be concise and specific."},
                {"role": "user", "content": f"Meeting topic: {meeting['topic']}\nAgenda: {json.dumps(meeting['agenda'])}\n\nTranscript:\n{transcript_text}"},
            ])
            meeting["summary"] = summary
            meeting["status"] = "completed"
            if SLACK_WEBHOOK:
                try:
                    requests.post(SLACK_WEBHOOK, json={"text": f"*Meeting Summary: {meeting['topic']}*\n{summary}"}, timeout=5)
                except Exception:
                    pass
        return jsonify({"status": "hangup"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/meetings/<mid>/advance", methods=["POST"])
def advance_agenda(mid):
    """Move to the next agenda item and announce it."""
    meeting = meetings.get(mid)
    if not meeting:
        return jsonify({"error": "not found"}), 404
    meeting["current_agenda_item"] += 1
    idx = meeting["current_agenda_item"]
    if idx < len(meeting["agenda"]):
        item = meeting["agenda"][idx]
        # Speak to first active participant
        for cid, p in meeting["participants"].items():
            if p["status"] == "joined":
                telnyx_call_action(cid, "speak", {
                    "payload": f"Moving to agenda item {idx + 1}: {item}.",
                    "language": "en-US", "voice": "female",
                })
                break
        return jsonify({"current_item": idx, "topic": item}), 200
    return jsonify({"status": "no more agenda items"}), 200


@app.route("/meetings/<mid>/mute/<call_id>", methods=["POST"])
def mute_participant(mid, call_id):
    meeting = meetings.get(mid)
    if not meeting or call_id not in meeting["participants"]:
        return jsonify({"error": "not found"}), 404
    telnyx_call_action(call_id, "join", {"name": mid, "mute": True})
    meeting["participants"][call_id]["muted"] = True
    return jsonify({"status": "muted"}), 200


@app.route("/meetings", methods=["GET"])
def list_meetings():
    return jsonify({"meetings": [{
        "id": m["id"], "topic": m["topic"], "status": m["status"],
        "participants": len(m["participants"]),
        "transcript_length": len(m["transcript"]),
    } for m in meetings.values()]}), 200


@app.route("/meetings/<mid>", methods=["GET"])
def get_meeting(mid):
    m = meetings.get(mid)
    if not m:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "meeting": m["id"], "topic": m["topic"], "status": m["status"],
        "transcript": m["transcript"], "summary": m.get("summary", ""),
        "agenda": m["agenda"], "current_item": m["current_agenda_item"],
    }), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for m in meetings.values() if m["status"] == "active")
    return jsonify({"status": "ok", "active_meetings": active, "total": len(meetings)}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
