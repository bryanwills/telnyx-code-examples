"""Edge Fraud Firewall — screen every inbound call at the edge before it reaches your app.
Runs number lookup, checks blocklist, classifies via AI inference. Clean calls pass through.
Suspicious calls route to a honeypot that wastes the scammer's time."""
import os, json, time, base64, hashlib, hmac, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
FORWARD_NUMBER = os.getenv("FORWARD_NUMBER")
HONEYPOT_CONNECTION = os.getenv("HONEYPOT_CONNECTION_ID", "")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

blocklist = set()
call_screening = {}
MAX_ENTRIES = 10000

def ttl_cleanup(store, max_size=MAX_ENTRIES):
    if len(store) > max_size:
        oldest = sorted(store, key=lambda k: store[k].get("ts", 0))
        for k in oldest[:len(store) - max_size]:
            del store[k]

def encode_state(data):
    return base64.b64encode(json.dumps(data).encode()).decode()

def decode_state(b64):
    try:
        return json.loads(base64.b64decode(b64).decode())
    except Exception:
        return {}

def lookup_number(phone):
    """Check number reputation via Telnyx Number Lookup."""
    try:
        resp = requests.get(
            f"https://api.telnyx.com/v2/number_lookup/{phone}",
            headers=HEADERS, timeout=10
        )
        if resp.ok:
            return resp.json().get("data", {})
    except Exception as e:
        app.logger.error("Number lookup failed: %s", e)
    return {}

def classify_caller(phone, lookup_data):
    """Use AI to classify caller risk based on lookup data."""
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": "You are a fraud detection system. Analyze caller data and respond with ONLY one word: CLEAN, SUSPICIOUS, or BLOCK."},
                         {"role": "user", "content": f"Caller: {phone}\nCarrier: {lookup_data.get('carrier', {}).get('name', 'unknown')}\nType: {lookup_data.get('carrier', {}).get('type', 'unknown')}\nCountry: {lookup_data.get('country_code', 'unknown')}"}]
        })
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip().upper()
    except Exception as e:
        app.logger.error("Classification failed: %s", e)
    return "CLEAN"

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    call_control_id = event.get("payload", {}).get("call_control_id")
    if not call_control_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.initiated":
        direction = event.get("payload", {}).get("direction")
        caller = event.get("payload", {}).get("from", "")
        if direction == "incoming":
            if caller in blocklist:
                app.logger.info("Blocked known bad caller: %s", caller)
                requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/reject",
                              headers=HEADERS, timeout=10)
                return jsonify({"status": "blocked"})

            lookup = lookup_number(caller)
            risk = classify_caller(caller, lookup)
            call_screening[call_control_id] = {"phone": caller, "risk": risk, "lookup": lookup, "ts": time.time()}
            ttl_cleanup(call_screening)

            if risk == "BLOCK":
                blocklist.add(caller)
                requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/reject",
                              headers=HEADERS, timeout=10)
                return jsonify({"status": "blocked"})
            elif risk == "SUSPICIOUS" and HONEYPOT_CONNECTION:
                requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/answer",
                              headers=HEADERS, timeout=10,
                              json={"client_state": encode_state({"flow": "honeypot"})})
            else:
                requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/answer",
                              headers=HEADERS, timeout=10,
                              json={"client_state": encode_state({"flow": "forward"})})

    elif event_type == "call.answered":
        state = decode_state(event.get("payload", {}).get("client_state", ""))
        flow = state.get("flow", "forward")
        if flow == "honeypot":
            requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": "Please hold while I connect you to a specialist.",
                                "voice": "female", "language": "en-US",
                                "client_state": encode_state({"flow": "honeypot_hold"})})
        else:
            if FORWARD_NUMBER:
                requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/transfer",
                              headers=HEADERS, timeout=10,
                              json={"to": FORWARD_NUMBER})
            else:
                requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/speak",
                              headers=HEADERS, timeout=10,
                              json={"payload": "Welcome. Your call has been verified.",
                                    "voice": "female", "language": "en-US"})

    elif event_type == "call.speak.ended":
        state = decode_state(event.get("payload", {}).get("client_state", ""))
        if state.get("flow") == "honeypot_hold":
            time.sleep(2)
            requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": "All specialists are currently busy. Please continue to hold.",
                                "voice": "female", "language": "en-US",
                                "client_state": encode_state({"flow": "honeypot_hold"})})

    elif event_type == "call.hangup":
        call_screening.pop(call_control_id, None)

    return jsonify({"status": "ok"})

@app.route("/blocklist", methods=["GET"])
def get_blocklist():
    return jsonify({"blocklist": sorted(blocklist), "count": len(blocklist)})

@app.route("/blocklist", methods=["POST"])
def add_to_blocklist():
    data = request.get_json() or {}
    phone = data.get("phone")
    if not phone:
        return jsonify({"error": "phone required"}), 400
    blocklist.add(phone)
    return jsonify({"status": "added", "phone": phone})

@app.route("/stats", methods=["GET"])
def stats():
    return jsonify({
        "active_screenings": len(call_screening),
        "blocklist_size": len(blocklist)
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-fraud-firewall"})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
