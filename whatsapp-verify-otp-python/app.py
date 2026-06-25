#!/usr/bin/env python3
"""WhatsApp Verify OTP — Send and verify one-time passwords via WhatsApp using the Telnyx Verify API."""
import os, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import threading, time as _ttl_time
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
VERIFY_PROFILE_ID = os.getenv("VERIFY_PROFILE_ID")
verifications = {}
webhook_events = []

def _start_ttl_cleanup(*stores, ttl_seconds=3600, interval=300):
    def _cleanup():
        while True:
            _ttl_time.sleep(interval)
            cutoff = _ttl_time.time() - ttl_seconds
            for store in stores:
                if isinstance(store, dict):
                    expired = [k for k, v in store.items()
                               if isinstance(v, dict) and v.get("_ts", _ttl_time.time()) < cutoff]
                    for k in expired:
                        store.pop(k, None)
                elif isinstance(store, list):
                    store[:] = [e for e in store
                                if isinstance(e, dict) and e.get("_ts", _ttl_time.time()) >= cutoff]
    threading.Thread(target=_cleanup, daemon=True).start()

_start_ttl_cleanup(verifications, webhook_events)


@app.route("/verify/start", methods=["POST"])
def start_verification():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    phone = data.get("phone_number")
    if not phone:
        return jsonify({"error": "phone_number required"}), 400
    try:
        resp = requests.post("https://api.telnyx.com/v2/verifications", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"phone_number": phone, "verify_profile_id": VERIFY_PROFILE_ID, "type": "whatsapp"}, timeout=10)
        if resp.ok:
            verifications[phone] = {"status": "pending", "channel": "whatsapp", "started": time.time(), "_ts": time.time()}
            return jsonify({"status": "sent", "phone": phone, "channel": "whatsapp"}), 200
        return jsonify({"error": resp.text}), resp.status_code
    except Exception as e:
        app.logger.exception("Failed to start verification")
        return jsonify({"error": "could not start verification"}), 500

@app.route("/verify/check", methods=["POST"])
def check_verification():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    phone = data.get("phone_number")
    code = data.get("code")
    if not phone or not code:
        return jsonify({"error": "phone_number and code required"}), 400
    try:
        resp = requests.post("https://api.telnyx.com/v2/verifications/by_phone_number/" + phone + "/actions/verify",
            headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"code": code}, timeout=10)
        if resp.ok:
            verifications[phone] = {"status": "verified", "verified_at": time.time(), "_ts": time.time()}
            return jsonify({"status": "verified"}), 200
        return jsonify({"status": "invalid_code"}), 400
    except Exception as e:
        app.logger.exception("Failed to check verification")
        return jsonify({"error": "could not verify code"}), 500

@app.route("/webhooks/verify", methods=["POST"])
def verify_webhook():
    payload = request.get_json()
    if not payload:
        return jsonify({"status": "ignored"}), 200
    event_type = payload.get("data", {}).get("event_type", "")
    phone = payload.get("data", {}).get("payload", {}).get("phone_number", "")
    app.logger.info("Webhook received: %s for %s", event_type, phone)
    webhook_events.append({"event": event_type, "phone": phone, "received_at": time.time(), "_ts": time.time()})
    if phone and phone in verifications:
        if event_type == "verify.sent":
            verifications[phone]["status"] = "sent"
        elif event_type == "verify.delivered":
            verifications[phone]["status"] = "delivered"
        elif event_type == "verify.completed":
            verifications[phone]["status"] = "completed"
        elif event_type == "verify.failed":
            verifications[phone]["status"] = "failed"
    return jsonify({"status": "ok"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "verifications": len(verifications)}), 200

if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
