#!/usr/bin/env python3
"""Warm Transfer with AI Briefing — when an agent transfers a call, AI summarizes the conversation and briefs the next agent before connecting them. No cold handoffs."""
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
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

calls = {}
transfer_queue = {}


def telnyx_post(path, data):
    resp = requests.post(f"{API}{path}", headers=HEADERS, json=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def telnyx_call_action(call_id, action, data=None):
    return telnyx_post(f"/calls/{call_id}/actions/{action}", data or {})


def call_inference(messages, max_tokens=200):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


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

    if event == "call.initiated" and data.get("direction") == "incoming":
        telnyx_call_action(call_id, "answer")
        calls[call_id] = {
            "transcript": [],
            "caller": data.get("from", ""),
            "started_at": time.time(),
            "status": "active",
        }
        return jsonify({"status": "answering"}), 200

    if event == "call.answered":
        role = client_state.get("role", "")
        if role == "next_agent":
            # This is the agent being transferred to — brief them first
            transfer_id = client_state.get("transfer_id", "")
            transfer = transfer_queue.get(transfer_id, {})
            briefing = transfer.get("briefing", "No context available.")

            telnyx_call_action(call_id, "speak", {
                "payload": f"Incoming transfer briefing: {briefing}. Press 1 to accept the call, or 2 to decline.",
                "language": "en-US",
                "voice": "female",
            })
            transfer["next_agent_call_id"] = call_id
            return jsonify({"status": "briefing_agent"}), 200

        # Regular call — start gathering speech
        telnyx_call_action(call_id, "gather_using_speak", {
            "payload": "Thank you for calling. How can I help you today?",
            "language": "en-US", "voice": "female",
            "inter_digit_timeout": 15, "minimum_digits": 1,
            "valid_digits": "0123456789*#",
        })
        return jsonify({"status": "answered"}), 200

    if event == "call.gather.ended":
        speech = data.get("speech", {}).get("result", "")
        digits = data.get("digits", "")
        role = client_state.get("role", "")

        if role == "next_agent":
            transfer_id = client_state.get("transfer_id", "")
            transfer = transfer_queue.get(transfer_id, {})
            if digits == "1":
                # Accept — bridge the caller into a conference with new agent
                conf_name = f"transfer-{transfer_id}"
                # Join next agent
                telnyx_call_action(call_id, "join", {
                    "name": conf_name, "start_conference_on_create": True,
                })
                # Join original caller
                original_call_id = transfer.get("original_call_id")
                if original_call_id:
                    try:
                        telnyx_call_action(original_call_id, "join", {"name": conf_name})
                    except Exception:
                        pass
                transfer["status"] = "connected"
            elif digits == "2":
                telnyx_call_action(call_id, "speak", {
                    "payload": "Transfer declined. The caller will be returned to the queue.",
                    "language": "en-US", "voice": "female",
                })
                transfer["status"] = "declined"
            return jsonify({"status": "transfer_decision"}), 200

        # Regular conversation — record transcript
        if speech and call_id in calls:
            calls[call_id]["transcript"].append({
                "time": time.time(), "speaker": "caller", "text": speech,
            })
        return jsonify({"status": "gathered"}), 200

    if event == "call.hangup":
        if call_id in calls:
            calls[call_id]["status"] = "ended"
        return jsonify({"status": "hangup"}), 200

    return jsonify({"status": "ok"}), 200


@app.route("/transfers/initiate", methods=["POST"])
def initiate_transfer():
    """Initiate a warm transfer with AI briefing."""
    data = request.get_json() or {}
    original_call_id = data.get("call_id")
    next_agent_phone = data.get("next_agent")
    reason = data.get("reason", "")

    call = calls.get(original_call_id)
    if not call:
        return jsonify({"error": "call not found"}), 404

    # Generate AI briefing from conversation so far
    transcript_text = "\n".join([f"{t['speaker']}: {t['text']}" for t in call["transcript"]])
    briefing = call_inference([
        {"role": "system", "content": "Generate a 2-sentence briefing for the next agent receiving this transferred call. Include: what the caller needs, what's been tried, and their emotional state. Be direct and actionable."},
        {"role": "user", "content": f"Transfer reason: {reason}\n\nConversation so far:\n{transcript_text}"},
    ])

    transfer_id = f"tx-{int(time.time())}"
    transfer_queue[transfer_id] = {
        "original_call_id": original_call_id,
        "briefing": briefing,
        "reason": reason,
        "next_agent_phone": next_agent_phone,
        "status": "dialing",
        "created_at": time.time(),
    }

    # Put caller on hold with music/message
    telnyx_call_action(original_call_id, "speak", {
        "payload": "I'm connecting you with a specialist now. Please hold for just a moment.",
        "language": "en-US", "voice": "female",
    })

    # Dial next agent
    telnyx_post("/calls", {
        "connection_id": CONNECTION_ID,
        "from": MAIN_NUMBER,
        "to": next_agent_phone,
        "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
        "client_state": base64.b64encode(json.dumps({
            "role": "next_agent", "transfer_id": transfer_id,
        }).encode()).decode(),
    })

    return jsonify({"transfer_id": transfer_id, "briefing": briefing, "status": "dialing"}), 201


@app.route("/transfers", methods=["GET"])
def list_transfers():
    return jsonify({"transfers": [{
        "id": tid, "status": t["status"], "briefing": t["briefing"],
    } for tid, t in transfer_queue.items()]}), 200


@app.route("/calls", methods=["GET"])
def list_calls():
    return jsonify({"calls": [{
        "call_id": cid, "status": c["status"],
        "transcript_length": len(c["transcript"]),
        "duration": int(time.time() - c["started_at"]) if c["status"] == "active" else 0,
    } for cid, c in calls.items()]}), 200


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for c in calls.values() if c["status"] == "active")
    pending = sum(1 for t in transfer_queue.values() if t["status"] == "dialing")
    return jsonify({"status": "ok", "active_calls": active, "pending_transfers": pending}), 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
