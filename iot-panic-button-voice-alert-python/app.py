#!/usr/bin/env python3
"""IoT Panic Button Voice Alert — IoT device triggers SIM-based alert, system calls emergency contacts with location and status."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
ALERT_NUMBER = os.getenv("ALERT_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
alerts = []
devices = {"DEV-001": {"name": "Warehouse A Panic Button", "location": "Building 3, Floor 1", "contacts": ["+15551234567", "+15559876543"]},
    "DEV-002": {"name": "Parking Lot B", "location": "North lot, near entrance", "contacts": ["+15551234567"]}}

@app.route("/alert", methods=["POST"])
def trigger_alert():
    data = request.get_json()
    device_id = data.get("device_id")
    device = devices.get(device_id)
    if not device: return jsonify({"error": "Unknown device"}), 404
    alert_id = f"ALERT-{int(time.time())}"
    alert = {"id": alert_id, "device_id": device_id, "device_name": device["name"], "location": device["location"],
        "triggered": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "active", "calls_made": []}
    for contact in device["contacts"]:
        try:
            resp = requests.post("https://api.telnyx.com/v2/calls", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                json={"to": contact, "from": ALERT_NUMBER, "connection_id": CONNECTION_ID,
                    "client_state": json.dumps({"alert_id": alert_id, "device": device["name"], "location": device["location"]}).encode().hex()}, timeout=10)
            alert["calls_made"].append({"contact": contact, "status": "calling"})
        except Exception:
            alert["calls_made"].append({"contact": contact, "status": "failed"})
        try:
            requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                json={"from": ALERT_NUMBER, "to": contact, "text": f"PANIC ALERT: {device['name']} at {device['location']}. Alert ID: {alert_id}. Respond immediately."}, timeout=10)
        except Exception: pass
    alerts.append(alert)
    return jsonify({"alert_id": alert_id, "contacts_notified": len(device["contacts"])}), 200

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    cs_hex = data.get("client_state", "")
    cs = {}
    if cs_hex:
        try: cs = json.loads(bytes.fromhex(cs_hex).decode())
        except Exception: pass
    if event_type == "call.answered":
        device = cs.get("device", "unknown device")
        location = cs.get("location", "unknown location")
        client.calls.actions.speak(ccid, payload=f"Emergency alert! Panic button activated at {device}, location: {location}. Press 1 to acknowledge, 2 to escalate to emergency services.", voice="female", language_code="en-US")
        return jsonify({"status": "alerting"}), 200
    elif event_type == "call.speak.ended":
        client.calls.actions.gather(ccid, input_type="dtmf", timeout_secs=15, min_digits=1, max_digits=1)
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended":
        digits = data.get("digits", "")
        if digits == "1":
            client.calls.actions.speak(ccid, payload="Alert acknowledged. Dispatch team notified. Stay safe.", voice="female", language_code="en-US")
        elif digits == "2":
            client.calls.actions.speak(ccid, payload="Escalating to emergency services. Please stay on the line.", voice="female", language_code="en-US")
        return jsonify({"status": "acknowledged"}), 200
    elif event_type == "call.hangup":
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/devices", methods=["POST"])
def register_device():
    data = request.get_json()
    did = data.get("device_id", f"DEV-{int(time.time())}")
    devices[did] = {"name": data.get("name"), "location": data.get("location"), "contacts": data.get("contacts", [])}
    return jsonify({"device_id": did}), 200

@app.route("/alerts", methods=["GET"])
def list_alerts():
    return jsonify({"alerts": alerts[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for a in alerts if a.get("status") == "active")
    return jsonify({"status": "ok", "devices": len(devices), "active_alerts": active}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
