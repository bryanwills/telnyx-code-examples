#!/usr/bin/env python3
"""AI Deposition Assistant — joins legal deposition calls, produces real-time transcript, flags objectionable questions, tracks exhibits mentioned, and generates structured deposition summary."""
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

depositions = {}


def telnyx_post(path, data):
    resp = requests.post(f"{API}{path}", headers=HEADERS, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def telnyx_call_action(call_id, action, data=None):
    return telnyx_post(f"/calls/{call_id}/actions/{action}", data or {})


def call_inference(messages, max_tokens=300):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


@app.route("/depositions/start", methods=["POST"])
def start_deposition():
    data = request.get_json() or {}
    dep_id = f"dep-{int(time.time())}"
    deposition = {
        "id": dep_id,
        "case": data.get("case_name", ""),
        "deponent": data.get("deponent", ""),
        "participants": {},
        "transcript": [],
        "exhibits_referenced": [],
        "objections_flagged": [],
        "started_at": time.time(),
        "status": "starting",
    }
    depositions[dep_id] = deposition

    for entry in data.get("participants", []):
        phone = entry.get("phone", entry) if isinstance(entry, dict) else entry
        role = entry.get("role", "attorney") if isinstance(entry, dict) else "attorney"
        resp = telnyx_post("/calls", {
            "connection_id": CONNECTION_ID,
            "from": MAIN_NUMBER,
            "to": phone,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
            "client_state": base64.b64encode(json.dumps({
                "deposition": dep_id, "role": role,
            }).encode()).decode(),
        })
        call_id = resp.get("data", {}).get("call_control_id", "")
        deposition["participants"][call_id] = {"phone": phone, "role": role, "status": "dialing"}

    return jsonify({"deposition_id": dep_id, "case": deposition["case"]}), 201


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

    dep_id = client_state.get("deposition", "")
    dep = depositions.get(dep_id)
    if not dep:
        return jsonify({"status": "no_deposition"}), 200

    if event == "call.answered":
        telnyx_call_action(call_id, "join", {
            "name": dep_id,
            "start_conference_on_create": True,
            "hold": False, "mute": False,
            "supervisor_role": "none",
        })
        if call_id in dep["participants"]:
            dep["participants"][call_id]["status"] = "joined"

        joined = sum(1 for p in dep["participants"].values() if p["status"] == "joined")
        if joined >= 2 and dep["status"] == "starting":
            dep["status"] = "on_record"
            telnyx_call_action(call_id, "speak", {
                "payload": f"AI court reporter active for deposition in the matter of {dep['case']}. Deponent: {dep['deponent']}. All statements are being transcribed. Counsel, please state your appearances.",
                "language": "en-US", "voice": "female",
            })
        return jsonify({"status": "joined"}), 200

    if event == "call.speak.ended":
        telnyx_call_action(call_id, "gather_using_speak", {
            "payload": " ",
            "language": "en-US", "voice": "female",
            "minimum_digits": 1, "maximum_digits": 1,
            "inter_digit_timeout": 30,
            "valid_digits": "0123456789*#",
            "client_state": base64.b64encode(json.dumps({
                "deposition": dep_id,
            }).encode()).decode(),
        })
        return jsonify({"status": "listening"}), 200

    if event == "call.gather.ended":
        speech = data.get("speech", {}).get("result", "")
        if speech and dep:
            participant = dep["participants"].get(call_id, {})
            role = participant.get("role", "unknown")
            entry = {
                "line": len(dep["transcript"]) + 1,
                "time": time.time(),
                "speaker_role": role,
                "text": speech,
            }
            dep["transcript"].append(entry)

            # Check for exhibit references
            lower = speech.lower()
            if "exhibit" in lower:
                dep["exhibits_referenced"].append({
                    "line": entry["line"],
                    "text": speech,
                    "time": time.time(),
                })

            # Flag potentially objectionable questions
            if role == "attorney" and "?" in speech:
                analysis = call_inference([
                    {"role": "system", "content": "You are a legal AI assistant monitoring a deposition. Analyze this question for common objection grounds: leading, compound, assumes facts not in evidence, calls for speculation, argumentative, asked and answered, relevance. If objectionable, state the ground in 5 words or less. If fine, say 'CLEAN'."},
                    {"role": "user", "content": speech},
                ])
                if "CLEAN" not in analysis.upper():
                    dep["objections_flagged"].append({
                        "line": entry["line"],
                        "question": speech,
                        "ground": analysis,
                        "time": time.time(),
                    })

            # Continue listening
            telnyx_call_action(call_id, "gather_using_speak", {
                "payload": " ",
                "language": "en-US", "voice": "female",
                "minimum_digits": 1, "maximum_digits": 1,
                "inter_digit_timeout": 30,
                "valid_digits": "0123456789*#",
                "client_state": base64.b64encode(json.dumps({
                    "deposition": dep_id,
                }).encode()).decode(),
            })
        return jsonify({"status": "transcribed"}), 200

    if event == "call.hangup":
        if call_id in dep["participants"]:
            dep["participants"][call_id]["status"] = "left"

        active = [p for p in dep["participants"].values() if p["status"] == "joined"]
        if not active and dep["transcript"]:
            dep["status"] = "completed"
            transcript_text = "\n".join([f"L{t['line']} [{t['speaker_role']}]: {t['text']}" for t in dep["transcript"]])
            summary = call_inference([
                {"role": "system", "content": "Generate a structured deposition summary including: 1) Key testimony points, 2) Admissions made, 3) Exhibits referenced, 4) Objections raised, 5) Contradictions or inconsistencies, 6) Areas for follow-up. Use line references."},
                {"role": "user", "content": f"Case: {dep['case']}\nDeponent: {dep['deponent']}\n\n{transcript_text}"},
            ])
            dep["summary"] = summary
        return jsonify({"status": "completed"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/depositions/<did>", methods=["GET"])
def get_deposition(did):
    d = depositions.get(did)
    if not d:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "deposition": d["id"], "case": d["case"], "deponent": d["deponent"],
        "status": d["status"], "lines": len(d["transcript"]),
        "exhibits": d["exhibits_referenced"],
        "objections": d["objections_flagged"],
        "summary": d.get("summary", ""),
    }), 200


@app.route("/depositions/<did>/transcript", methods=["GET"])
def get_dep_transcript(did):
    d = depositions.get(did)
    if not d:
        return jsonify({"error": "not found"}), 404
    return jsonify({"transcript": d["transcript"]}), 200


@app.route("/depositions", methods=["GET"])
def list_depositions():
    return jsonify({"depositions": [{
        "id": d["id"], "case": d["case"], "status": d["status"],
        "lines": len(d["transcript"]),
    } for d in depositions.values()]}), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for d in depositions.values() if d["status"] == "on_record")
    return jsonify({"status": "ok", "active_depositions": active, "total": len(depositions)}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
