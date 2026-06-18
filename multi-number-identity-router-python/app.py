#!/usr/bin/env python3
"""Multi-Number Identity Router — route calls based on which number was dialed. Each number maps to a different business identity, greeting, and routing destination."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
CONNECTION_ID = os.getenv("CONNECTION_ID")
call_log = []

identities = {
    "+15551001001": {"name": "Acme Sales", "greeting": "Thanks for calling Acme Sales! How can I help you today?", "forward_to": "+15559999001", "hours": "9-17"},
    "+15551001002": {"name": "Acme Support", "greeting": "Acme Support here. What issue are you experiencing?", "forward_to": "+15559999002", "hours": "24/7"},
    "+15551001003": {"name": "Acme Billing", "greeting": "Acme Billing department. I can help with your account.", "forward_to": "+15559999003", "hours": "9-17"},
}

@app.route("/identities", methods=["POST"])
def add_identity():
    data = request.get_json()
    number = data.get("number")
    identities[number] = {"name": data.get("name"), "greeting": data.get("greeting"), "forward_to": data.get("forward_to"), "hours": data.get("hours", "24/7")}
    return jsonify({"status": "added", "number": number}), 200

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        dialed = data.get("to")
        identity = identities.get(dialed, {"name": "Default", "greeting": "Hello, how can I help?", "forward_to": None})
        call_log.append({"dialed": dialed, "identity": identity["name"], "caller": data.get("from"), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering", "identity": identity["name"]}), 200
    elif event_type == "call.answered":
        dialed = data.get("to", "")
        identity = identities.get(dialed, {"greeting": "Hello!", "forward_to": None})
        client.calls.actions.speak(ccid, payload=identity["greeting"], voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended":
        dialed = data.get("to", "")
        identity = identities.get(dialed, {})
        if identity.get("forward_to"):
            client.calls.actions.transfer(ccid, to=identity["forward_to"])
        return jsonify({"status": "forwarding"}), 200
    elif event_type == "call.hangup":
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/identities", methods=["GET"])
def list_identities():
    return jsonify({"identities": {k: {"name": v["name"], "hours": v["hours"]} for k, v in identities.items()}}), 200

@app.route("/calls", methods=["GET"])
def list_calls():
    return jsonify({"calls": call_log[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "identities": len(identities)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
