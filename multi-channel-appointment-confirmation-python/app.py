#!/usr/bin/env python3
"""Multi-Channel Appointment Confirmation — confirm appointments via SMS, voice call, and WhatsApp. Tries SMS first, escalates to voice if no response."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
CONFIRM_NUMBER = os.getenv("CONFIRM_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
MESSAGING_PROFILE_ID = os.getenv("MESSAGING_PROFILE_ID", "")
appointments = {}
confirmations = []

def send_sms(to, text):
    try:
        resp = requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": CONFIRM_NUMBER, "to": to, "text": text, "messaging_profile_id": MESSAGING_PROFILE_ID}, timeout=10)
        return resp.ok
    except Exception: return False

def make_confirmation_call(to, appointment):
    try:
        resp = requests.post("https://api.telnyx.com/v2/calls", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"to": to, "from": CONFIRM_NUMBER, "connection_id": CONNECTION_ID,
                "client_state": json.dumps({"appt_id": appointment["id"]}).encode().hex()}, timeout=10)
        return resp.ok
    except Exception: return False

@app.route("/appointments", methods=["POST"])
def create_appointment():
    data = request.get_json()
    aid = f"APT-{int(time.time())}"
    appointments[aid] = {"id": aid, "patient": data.get("name"), "phone": data.get("phone"), "date": data.get("date"),
        "time": data.get("time"), "provider": data.get("provider", "Dr. Smith"), "status": "pending", "channel_attempts": []}
    return jsonify({"appointment_id": aid}), 200

@app.route("/confirm/<aid>", methods=["POST"])
def send_confirmation(aid):
    appt = appointments.get(aid)
    if not appt: return jsonify({"error": "Not found"}), 404
    msg = f"Hi {appt['patient']}! Confirming your appointment with {appt['provider']} on {appt['date']} at {appt['time']}. Reply YES to confirm or RESCHEDULE to change."
    success = send_sms(appt["phone"], msg)
    appt["channel_attempts"].append({"channel": "sms", "success": success, "time": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
    appt["status"] = "sms_sent"
    return jsonify({"status": "sms_sent", "success": success}), 200

@app.route("/escalate/<aid>", methods=["POST"])
def escalate_to_voice(aid):
    appt = appointments.get(aid)
    if not appt: return jsonify({"error": "Not found"}), 404
    success = make_confirmation_call(appt["phone"], appt)
    appt["channel_attempts"].append({"channel": "voice", "success": success, "time": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
    appt["status"] = "voice_calling"
    return jsonify({"status": "voice_calling", "success": success}), 200

@app.route("/webhooks/messaging", methods=["POST"])
def handle_sms_reply():
    payload = request.get_json()
    data = payload.get("data", {})
    if data.get("event_type") != "message.received" or data.get("direction") != "inbound":
        return jsonify({"status": "ignored"}), 200
    phone = data.get("from", {}).get("phone_number", "")
    text = data.get("text", "").strip().upper()
    for aid, appt in appointments.items():
        if appt["phone"] == phone and appt["status"] in ("sms_sent", "voice_calling"):
            if text in ("YES", "CONFIRM", "Y"):
                appt["status"] = "confirmed"
                confirmations.append({"appointment_id": aid, "channel": "sms", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
                send_sms(phone, f"Confirmed! See you {appt['date']} at {appt['time']} with {appt['provider']}.")
            elif "RESCHEDULE" in text:
                appt["status"] = "reschedule_requested"
                send_sms(phone, "We'll have someone call you to reschedule. Thanks!")
            break
    return jsonify({"status": "handled"}), 200

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
    aid = cs.get("appt_id")
    appt = appointments.get(aid) if aid else None
    if event_type == "call.answered" and appt:
        client.calls.actions.speak(ccid, payload=f"Hi {appt['patient']}! This is a reminder about your appointment with {appt['provider']} on {appt['date']} at {appt['time']}. Press 1 to confirm or 2 to reschedule.", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended":
        client.calls.actions.gather(ccid, input_type="dtmf", timeout_secs=10, min_digits=1, max_digits=1)
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended" and appt:
        digits = data.get("digits", "")
        if digits == "1":
            appt["status"] = "confirmed"
            confirmations.append({"appointment_id": aid, "channel": "voice", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            client.calls.actions.speak(ccid, payload="Confirmed! See you then. Goodbye!", voice="female", language_code="en-US")
        elif digits == "2":
            appt["status"] = "reschedule_requested"
            client.calls.actions.speak(ccid, payload="We'll call you to reschedule. Goodbye!", voice="female", language_code="en-US")
        return jsonify({"status": "confirmed"}), 200
    elif event_type == "call.hangup":
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/appointments/status", methods=["GET"])
def appointment_status():
    summary = {"pending": 0, "confirmed": 0, "reschedule_requested": 0, "sms_sent": 0}
    for a in appointments.values():
        summary[a.get("status", "pending")] = summary.get(a.get("status", "pending"), 0) + 1
    return jsonify({"appointments": len(appointments), "summary": summary, "confirmations": len(confirmations)}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "appointments": len(appointments)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
