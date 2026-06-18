#!/usr/bin/env python3
"""AI Meeting Action Tracker — joins a multi-party call, identifies speakers, extracts action items with owners and deadlines, and posts structured notes to Slack when the call ends."""
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


def call_inference(messages, max_tokens=400):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.4}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def post_slack(text):
    if SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=5)
        except Exception:
            pass


@app.route("/meetings/create", methods=["POST"])
def create_meeting():
    data = request.get_json() or {}
    meeting_id = f"mtg-{int(time.time())}"
    meeting = {
        "id": meeting_id,
        "title": data.get("title", "Untitled Meeting"),
        "participants": {},
        "transcript": [],
        "action_items": [],
        "decisions": [],
        "created_at": time.time(),
        "status": "pending",
    }
    meetings[meeting_id] = meeting

    for phone in data.get("participants", []):
        resp = telnyx_post("/calls", {
            "connection_id": CONNECTION_ID,
            "from": MAIN_NUMBER,
            "to": phone,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
            "client_state": base64.b64encode(json.dumps({"meeting": meeting_id}).encode()).decode(),
        })
        call_id = resp.get("data", {}).get("call_control_id", "")
        meeting["participants"][call_id] = {"phone": phone, "status": "dialing"}

    return jsonify({"meeting_id": meeting_id}), 201


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
        telnyx_call_action(call_id, "join", {
            "name": meeting_id,
            "start_conference_on_create": True,
            "hold": False, "mute": False,
            "supervisor_role": "none",
        })
        if call_id in meeting["participants"]:
            meeting["participants"][call_id]["status"] = "joined"

        joined = sum(1 for p in meeting["participants"].values() if p["status"] == "joined")
        if joined >= 2 and meeting["status"] == "pending":
            meeting["status"] = "active"
            meeting["started_at"] = time.time()
            telnyx_call_action(call_id, "speak", {
                "payload": f"Meeting started: {meeting['title']}. I'm tracking action items and decisions. Speak naturally.",
                "language": "en-US", "voice": "female",
            })
        return jsonify({"status": "joined"}), 200

    if event == "call.speak.ended":
        telnyx_call_action(call_id, "gather_using_speak", {
            "payload": " ",
            "language": "en-US", "voice": "female",
            "minimum_digits": 1, "maximum_digits": 1,
            "inter_digit_timeout": 20,
            "valid_digits": "0123456789*#",
            "client_state": base64.b64encode(json.dumps({"meeting": meeting_id}).encode()).decode(),
        })
        return jsonify({"status": "listening"}), 200

    if event == "call.gather.ended":
        speech = data.get("speech", {}).get("result", "")
        if speech and meeting:
            participant = meeting["participants"].get(call_id, {})
            phone = participant.get("phone", "unknown")[-4:]
            meeting["transcript"].append({
                "time": time.time(),
                "speaker": f"...{phone}",
                "text": speech,
            })

            # Every 5 turns, extract incremental action items
            if len(meeting["transcript"]) % 5 == 0:
                recent = "\n".join([f"{t['speaker']}: {t['text']}" for t in meeting["transcript"][-10:]])
                extraction = call_inference([
                    {"role": "system", "content": "Extract action items and decisions from this meeting segment. Format: ACTION: [owner] - [task] - [deadline if mentioned]. DECISION: [what was decided]. If none, say NONE."},
                    {"role": "user", "content": recent},
                ])
                if "NONE" not in extraction.upper():
                    for line in extraction.strip().split("\n"):
                        line = line.strip()
                        if line.startswith("ACTION:"):
                            meeting["action_items"].append({"text": line[7:].strip(), "extracted_at": time.time()})
                        elif line.startswith("DECISION:"):
                            meeting["decisions"].append({"text": line[9:].strip(), "extracted_at": time.time()})

        # Continue listening
        telnyx_call_action(call_id, "gather_using_speak", {
            "payload": " ",
            "language": "en-US", "voice": "female",
            "minimum_digits": 1, "maximum_digits": 1,
            "inter_digit_timeout": 20,
            "valid_digits": "0123456789*#",
            "client_state": base64.b64encode(json.dumps({"meeting": meeting_id}).encode()).decode(),
        })
        return jsonify({"status": "processed"}), 200

    if event == "call.hangup":
        if call_id in meeting["participants"]:
            meeting["participants"][call_id]["status"] = "left"

        active = [p for p in meeting["participants"].values() if p["status"] == "joined"]
        if not active and meeting["transcript"]:
            meeting["status"] = "completed"
            duration = int((time.time() - meeting.get("started_at", time.time())) / 60)
            transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in meeting["transcript"]])

            notes = call_inference([
                {"role": "system", "content": "Generate structured meeting notes. Sections: Summary (3 sentences), Key Decisions, Action Items (owner | task | deadline), Open Questions, Parking Lot (topics deferred). Be specific and use speaker references."},
                {"role": "user", "content": f"Meeting: {meeting['title']}\nDuration: {duration} min\n\n{transcript_text}"},
            ])
            meeting["notes"] = notes

            slack_msg = f"*Meeting Notes: {meeting['title']}* ({duration} min)\n\n{notes}"
            if meeting["action_items"]:
                slack_msg += "\n\n*Action Items Tracked:*\n" + "\n".join([f"• {a['text']}" for a in meeting["action_items"]])
            post_slack(slack_msg)
        return jsonify({"status": "completed"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/meetings/<mid>", methods=["GET"])
def get_meeting(mid):
    m = meetings.get(mid)
    if not m:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "meeting": m["id"], "title": m["title"], "status": m["status"],
        "action_items": m["action_items"], "decisions": m["decisions"],
        "transcript_length": len(m["transcript"]),
        "notes": m.get("notes", ""),
    }), 200


@app.route("/meetings", methods=["GET"])
def list_meetings():
    return jsonify({"meetings": [{
        "id": m["id"], "title": m["title"], "status": m["status"],
        "action_items": len(m["action_items"]),
    } for m in meetings.values()]}), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for m in meetings.values() if m["status"] == "active")
    return jsonify({"status": "ok", "active": active, "total": len(meetings)}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
