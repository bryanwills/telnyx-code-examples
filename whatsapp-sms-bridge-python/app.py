#!/usr/bin/env python3
"""WhatsApp-SMS Bridge — receive messages on WhatsApp and forward them via SMS, and vice versa. Bidirectional bridge between two messaging channels."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
SMS_NUMBER = os.getenv("SMS_NUMBER")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
MESSAGING_PROFILE_ID = os.getenv("MESSAGING_PROFILE_ID", "")
bridges = {}
message_log = []

def send_sms(to, text):
    try:
        resp = requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": SMS_NUMBER, "to": to, "text": text, "messaging_profile_id": MESSAGING_PROFILE_ID}, timeout=10)
        return resp.ok
    except Exception: return False

def send_whatsapp(to, text):
    try:
        resp = requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": WHATSAPP_NUMBER, "to": to, "text": text, "messaging_profile_id": MESSAGING_PROFILE_ID, "type": "whatsapp"}, timeout=10)
        return resp.ok
    except Exception: return False

@app.route("/bridge", methods=["POST"])
def create_bridge():
    data = request.get_json()
    sms_user = data.get("sms_number")
    whatsapp_user = data.get("whatsapp_number")
    bridges[sms_user] = {"whatsapp": whatsapp_user, "direction": "sms_to_whatsapp"}
    bridges[whatsapp_user] = {"sms": sms_user, "direction": "whatsapp_to_sms"}
    return jsonify({"status": "bridged", "sms": sms_user, "whatsapp": whatsapp_user}), 200

@app.route("/webhooks/messaging", methods=["POST"])
def handle_message():
    payload = request.get_json()
    data = payload.get("data", {})
    if data.get("event_type") != "message.received" or data.get("direction") != "inbound":
        return jsonify({"status": "ignored"}), 200
    from_number = data.get("from", {}).get("phone_number", "")
    text = data.get("text", "")
    msg_type = data.get("type", "sms")
    bridge = bridges.get(from_number)
    if not bridge:
        return jsonify({"status": "no_bridge"}), 200
    log_entry = {"from": from_number, "text": text, "type": msg_type, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    if bridge.get("direction") == "sms_to_whatsapp":
        target = bridge["whatsapp"]
        success = send_whatsapp(target, f"[SMS from {from_number}] {text}")
        log_entry["forwarded_to"] = target
        log_entry["channel"] = "whatsapp"
    elif bridge.get("direction") == "whatsapp_to_sms":
        target = bridge["sms"]
        success = send_sms(target, f"[WhatsApp from {from_number}] {text}")
        log_entry["forwarded_to"] = target
        log_entry["channel"] = "sms"
    else:
        success = False
    log_entry["success"] = success
    message_log.append(log_entry)
    return jsonify({"status": "forwarded" if success else "failed"}), 200

@app.route("/bridges", methods=["GET"])
def list_bridges():
    return jsonify({"bridges": bridges}), 200

@app.route("/messages", methods=["GET"])
def list_messages():
    return jsonify({"messages": message_log[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bridges": len(bridges) // 2, "messages": len(message_log)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
