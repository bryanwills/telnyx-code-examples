"""Merge Employee Hotline - employees call, authenticate via caller ID against
Merge HRIS. AI pulls PTO balance, benefits, org chart. Answers conversationally."""
import os, json, time, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
MERGE_API_KEY = os.getenv("MERGE_API_KEY")
MERGE_ACCOUNT_TOKEN = os.getenv("MERGE_ACCOUNT_TOKEN")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {"Authorization": f"Bearer {MERGE_API_KEY}", "X-Account-Token": MERGE_ACCOUNT_TOKEN or "", "Content-Type": "application/json"}

call_sessions = {}
MAX_ENTRIES = 10000

def ttl_cleanup(store, max_size=MAX_ENTRIES):
    if len(store) > max_size:
        oldest = sorted(store, key=lambda k: store[k].get("ts", 0))
        for k in oldest[:len(store) - max_size]:
            del store[k]

def encode_state(data):
    return base64.b64encode(json.dumps(data).encode()).decode()

def decode_state(b64):
    try: return json.loads(base64.b64decode(b64).decode())
    except: return {}

# Telnyx public key (Portal > Keys & Credentials) is a base64-encoded 32-byte Ed25519 key.
_TELNYX_VERIFY_KEY = None
if TELNYX_PUBLIC_KEY:
    try:
        _TELNYX_VERIFY_KEY = Ed25519PublicKey.from_public_bytes(base64.b64decode(TELNYX_PUBLIC_KEY))
    except Exception as e:
        app.logger.error("Invalid TELNYX_PUBLIC_KEY, webhook verification disabled: %s", e)

MAX_SKEW_SECONDS = 300

def verify_telnyx_signature(raw_body, headers):
    """Verify the Telnyx Ed25519 signature over ``<timestamp>|<raw body>`` before
    trusting the webhook. Headers are telnyx-signature-ed25519 (base64) and
    telnyx-timestamp. Rejects signatures older than MAX_SKEW_SECONDS (replay)."""
    if _TELNYX_VERIFY_KEY is None:
        return False
    signature = headers.get("telnyx-signature-ed25519", "")
    timestamp = headers.get("telnyx-timestamp", "")
    if not signature or not timestamp:
        return False
    try:
        if abs(time.time() - int(timestamp)) > MAX_SKEW_SECONDS:
            return False
        signed = f"{timestamp}|".encode() + raw_body
        _TELNYX_VERIFY_KEY.verify(base64.b64decode(signature), signed)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False

def lookup_employee(phone):
    try:
        resp = requests.get("https://api.merge.dev/api/hris/v1/employees",
                            headers=MERGE_HEADERS, timeout=10,
                            params={"personal_phone_number": phone})
        if resp.ok:
            results = resp.json().get("results", [])
            if results:
                return results[0]
    except Exception as e:
        app.logger.error("Merge employee lookup failed: %s", e)
    return None

def get_time_off(employee_id):
    try:
        resp = requests.get("https://api.merge.dev/api/hris/v1/time-off",
                            headers=MERGE_HEADERS, timeout=10,
                            params={"employee_id": employee_id, "status": "APPROVED"})
        if resp.ok:
            return resp.json().get("results", [])
    except Exception as e:
        app.logger.error("Merge time-off lookup failed: %s", e)
    return []

def call_inference(question, employee_context):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": f"You are an HR assistant. Answer concisely in 1-2 sentences using this data: {json.dumps(employee_context)}"},
                {"role": "user", "content": question}
            ]
        })
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        app.logger.error("Inference failed: %s", e)
    return "I could not process that request right now."

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    # Verify the Telnyx Ed25519 signature against the RAW body before trusting anything.
    raw_body = request.get_data()
    if not verify_telnyx_signature(raw_body, request.headers):
        return jsonify({"error": "invalid signature"}), 401
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    ep = event.get("payload", {})
    cc_id = ep.get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.initiated" and ep.get("direction") == "incoming":
        caller = ep.get("from", "")
        employee = lookup_employee(caller)
        if employee:
            time_off = get_time_off(employee.get("id", ""))
            emp_data = {
                "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
                "department": str(employee.get("department", "Unknown")),
                "manager": str(employee.get("manager", "Unknown")),
                "hire_date": employee.get("hire_date", "Unknown"),
                "time_off_upcoming": [{"start": t.get("start_date"), "end": t.get("end_date")} for t in time_off[:5]]
            }
            call_sessions[cc_id] = {"employee": emp_data, "history": [], "ts": time.time()}
            ttl_cleanup(call_sessions)
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
                          headers=HEADERS, timeout=10,
                          json={"client_state": encode_state({"auth": True})})
        else:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
                          headers=HEADERS, timeout=10,
                          json={"client_state": encode_state({"auth": False})})

    elif event_type == "call.answered":
        state = decode_state(ep.get("client_state", ""))
        session = call_sessions.get(cc_id, {})
        if state.get("auth"):
            name = session.get("employee", {}).get("name", "")
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": f"Hi {name}. What would you like to know?",
                                "voice": "female", "language": "en-US", "input_type": "speech", "timeout_secs": 30,
                                "client_state": encode_state({"step": "conversation"})})
        else:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": "Could not verify your identity. Please call from your registered number.",
                                "voice": "female", "language": "en-US"})

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        session = call_sessions.get(cc_id, {})
        if speech and session.get("employee"):
            response = call_inference(speech, session["employee"])
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": response, "voice": "female", "language": "en-US",
                                "input_type": "speech", "timeout_secs": 30,
                                "client_state": encode_state({"step": "conversation"})})

    elif event_type == "call.speak.ended":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
                      headers=HEADERS, timeout=10)

    elif event_type == "call.hangup":
        call_sessions.pop(cc_id, None)

    return jsonify({"status": "ok"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-employee-hotline"})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
