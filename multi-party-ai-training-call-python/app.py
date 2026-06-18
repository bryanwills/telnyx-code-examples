#!/usr/bin/env python3
"""Multi-Party AI Training Call — AI plays customer roles for sales/support team practice. Multiple trainees join a conference, AI rotates through scenarios, and scores each trainee's performance."""
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

SCENARIOS = [
    {
        "name": "angry_billing",
        "persona": "You are Marcus, a frustrated customer who was double-charged $450 on his last invoice. You're angry but reasonable if the rep acknowledges the problem quickly. If they try to deflect or put you on hold, get angrier. You want: refund confirmed, explanation of how it happened, assurance it won't happen again.",
        "scoring_criteria": "empathy, speed to acknowledge, concrete resolution offered, de-escalation skill",
    },
    {
        "name": "competitor_switching",
        "persona": "You are Sarah, a technical lead evaluating Telnyx vs a competitor. You're currently on Twilio paying $800/month. You need: programmable voice, SMS, phone numbers in 5 countries. You have specific technical questions about latency, uptime SLA, and API compatibility. You're leaning toward switching but need convincing on reliability.",
        "scoring_criteria": "technical accuracy, competitive positioning, discovery questions asked, confidence without overselling",
    },
    {
        "name": "complex_onboarding",
        "persona": "You are Raj, a developer trying to set up voice AI for the first time. You've read the docs but are confused about the difference between Call Control and TeXML. You need help choosing the right approach for your use case: an IVR that routes to AI agents. You're technical but new to telecom.",
        "scoring_criteria": "clarity of explanation, correct technical guidance, patience, proactive next steps",
    },
]

sessions = {}


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


@app.route("/training/start", methods=["POST"])
def start_training():
    data = request.get_json() or {}
    session_id = f"train-{int(time.time())}"
    scenario_name = data.get("scenario", "angry_billing")
    scenario = next((s for s in SCENARIOS if s["name"] == scenario_name), SCENARIOS[0])

    session = {
        "id": session_id,
        "scenario": scenario,
        "trainees": {},
        "current_trainee": None,
        "conversation": [],
        "scores": {},
        "status": "pending",
        "created_at": time.time(),
    }
    sessions[session_id] = session

    for phone in data.get("trainees", []):
        resp = telnyx_post("/calls", {
            "connection_id": CONNECTION_ID,
            "from": MAIN_NUMBER,
            "to": phone,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
            "client_state": base64.b64encode(json.dumps({
                "session": session_id, "role": "trainee",
            }).encode()).decode(),
        })
        call_id = resp.get("data", {}).get("call_control_id", "")
        session["trainees"][call_id] = {"phone": phone, "status": "dialing", "turns": []}

    return jsonify({"session_id": session_id, "scenario": scenario_name}), 201


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

    session_id = client_state.get("session", "")
    session = sessions.get(session_id)
    if not session:
        return jsonify({"status": "no_session"}), 200

    if event == "call.answered":
        telnyx_call_action(call_id, "join", {
            "name": session_id,
            "start_conference_on_create": True,
            "hold": False, "mute": True,
            "supervisor_role": "none",
        })
        if call_id in session["trainees"]:
            session["trainees"][call_id]["status"] = "joined"

        joined = [cid for cid, t in session["trainees"].items() if t["status"] == "joined"]
        if len(joined) >= 1 and session["status"] == "pending":
            session["status"] = "active"
            first = joined[0]
            session["current_trainee"] = first

            # Unmute the active trainee
            telnyx_call_action(first, "join", {"name": session_id, "mute": False})

            scenario = session["scenario"]
            telnyx_call_action(first, "speak", {
                "payload": f"Training session starting. Scenario: {scenario['name'].replace('_', ' ')}. You're up first. The customer is calling now.",
                "language": "en-US", "voice": "female",
            })
        return jsonify({"status": "joined"}), 200

    if event == "call.speak.ended":
        # After AI speaks (either as moderator or as customer), listen for response
        if call_id == session.get("current_trainee"):
            telnyx_call_action(call_id, "gather_using_speak", {
                "payload": " ",
                "language": "en-US", "voice": "female",
                "minimum_digits": 1, "maximum_digits": 1,
                "inter_digit_timeout": 15,
                "valid_digits": "0123456789*#",
                "client_state": base64.b64encode(json.dumps({
                    "session": session_id, "role": "trainee",
                }).encode()).decode(),
            })
        return jsonify({"status": "listening"}), 200

    if event == "call.gather.ended":
        speech = data.get("speech", {}).get("result", "")
        if speech and session and call_id == session.get("current_trainee"):
            trainee = session["trainees"].get(call_id, {})
            trainee["turns"].append({"role": "trainee", "text": speech, "time": time.time()})

            # AI responds as customer
            scenario = session["scenario"]
            history = [{"role": "system", "content": scenario["persona"]}]
            for turn in trainee.get("turns", [])[-8:]:
                role = "assistant" if turn["role"] == "customer" else "user"
                history.append({"role": role, "content": turn["text"]})

            customer_response = call_inference(history, max_tokens=150)
            trainee["turns"].append({"role": "customer", "text": customer_response, "time": time.time()})

            # Check if scenario should end (after 6 exchanges)
            trainee_turns = [t for t in trainee["turns"] if t["role"] == "trainee"]
            if len(trainee_turns) >= 6:
                # Score and move to next trainee
                conversation_text = "\n".join([f"{t['role']}: {t['text']}" for t in trainee["turns"]])
                score = call_inference([
                    {"role": "system", "content": f"Score this trainee's performance on: {scenario['scoring_criteria']}. Rate each criterion 1-10. Give one specific thing they did well and one thing to improve. Be direct."},
                    {"role": "user", "content": conversation_text},
                ], max_tokens=250)
                session["scores"][call_id] = score

                # Announce score and rotate
                telnyx_call_action(call_id, "speak", {
                    "payload": f"Time's up. Here's your feedback: {score}",
                    "language": "en-US", "voice": "female",
                })

                # Mute current, find next
                telnyx_call_action(call_id, "join", {"name": session_id, "mute": True})
                next_trainees = [cid for cid, t in session["trainees"].items()
                                 if t["status"] == "joined" and cid not in session["scores"]]
                if next_trainees:
                    next_cid = next_trainees[0]
                    session["current_trainee"] = next_cid
                    telnyx_call_action(next_cid, "join", {"name": session_id, "mute": False})
                    telnyx_call_action(next_cid, "speak", {
                        "payload": "Your turn. The customer is calling now.",
                        "language": "en-US", "voice": "female",
                    })
                else:
                    session["status"] = "completed"
            else:
                telnyx_call_action(call_id, "speak", {
                    "payload": customer_response,
                    "language": "en-US", "voice": "female",
                })
        return jsonify({"status": "processed"}), 200

    if event == "call.hangup":
        if call_id in session["trainees"]:
            session["trainees"][call_id]["status"] = "left"
        return jsonify({"status": "hangup"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/training/<sid>", methods=["GET"])
def get_session_detail(sid):
    s = sessions.get(sid)
    if not s:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "session": s["id"], "scenario": s["scenario"]["name"],
        "status": s["status"], "scores": s["scores"],
        "trainees": len(s["trainees"]),
    }), 200


@app.route("/training", methods=["GET"])
def list_sessions_view():
    return jsonify({"sessions": [{
        "id": s["id"], "scenario": s["scenario"]["name"],
        "status": s["status"], "trainees": len(s["trainees"]),
        "scored": len(s["scores"]),
    } for s in sessions.values()]}), 200


@app.route("/scenarios", methods=["GET"])
def list_scenarios():
    return jsonify({"scenarios": [{"name": s["name"], "criteria": s["scoring_criteria"]} for s in SCENARIOS]}), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for s in sessions.values() if s["status"] == "active")
    return jsonify({"status": "ok", "active_sessions": active, "total": len(sessions), "scenarios": len(SCENARIOS)}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
