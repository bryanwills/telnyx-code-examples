"""Edge Merge Shift Coverage — manager texts need a closer tonight. Edge worker checks
HRIS schedule via Merge, calls available employees in priority order, negotiates,
confirms via SMS to both parties."""
import os, json, time, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
TELNYX_PHONE = os.getenv("TELNYX_PHONE_NUMBER")
CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
MERGE_API_KEY = os.getenv("MERGE_API_KEY")
MERGE_ACCOUNT_TOKEN = os.getenv("MERGE_ACCOUNT_TOKEN")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {"Authorization": f"Bearer {MERGE_API_KEY}", "X-Account-Token": MERGE_ACCOUNT_TOKEN or "", "Content-Type": "application/json"}
MERGE_BASE = "https://api.merge.dev/api"


def verify_telnyx_signature(body: bytes, headers, tolerance: int = 300) -> bool:
    """Verify the inbound Telnyx Ed25519 signature over "<timestamp>|<raw body>".

    Telnyx signs every webhook (telnyx-signature-ed25519 / telnyx-timestamp headers).
    Public key from Portal > Keys & Credentials. Rejects timestamps older than
    ``tolerance`` seconds (replay protection).
    """
    sig_b64 = headers.get("telnyx-signature-ed25519", "")
    timestamp = headers.get("telnyx-timestamp", "")
    if not (sig_b64 and timestamp and TELNYX_PUBLIC_KEY):
        return False
    try:
        if abs(time.time() - int(timestamp)) > tolerance:  # replay protection
            return False
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(TELNYX_PUBLIC_KEY))
        public_key.verify(base64.b64decode(sig_b64), f"{timestamp}|".encode() + body)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


shift_requests = {}
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

def merge_get(path, params=None):
    try:
        resp = requests.get(f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, params=params)
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge GET %s failed: %s", path, e)
    return None

def get_available_employees():
    result = merge_get("/hris/v1/employees", params={"employment_status": "ACTIVE", "page_size": 50})
    employees = (result or {}).get("results", [])
    available = []
    for emp in employees:
        phone = None
        for pn in emp.get("phone_numbers", []):
            if pn.get("value"):
                phone = pn["value"]
                break
        if phone:
            available.append({"id": emp.get("id"), "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(), "phone": phone})
    return available

def call_next_employee(shift_id):
    shift = shift_requests.get(shift_id)
    if not shift:
        return
    candidates = shift.get("candidates", [])
    idx = shift.get("current_idx", 0)
    if idx >= len(candidates):
        manager_phone = shift.get("manager_phone")
        if manager_phone:
            try:
                requests.post("https://api.telnyx.com/v2/messages", headers=HEADERS, timeout=10,
                              json={"from": TELNYX_PHONE, "to": manager_phone,
                                    "text": f"Could not fill shift: {shift.get('description', '')}. All candidates declined or unavailable."})
            except Exception as e:
                app.logger.error("Escalation SMS failed: %s", e)
        return
    candidate = candidates[idx]
    shift["current_idx"] = idx + 1
    try:
        resp = requests.post("https://api.telnyx.com/v2/calls", headers=HEADERS, timeout=10, json={
            "connection_id": CONNECTION_ID, "to": candidate["phone"], "from": TELNYX_PHONE,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice" if hasattr(request, "url_root") else ""
        })
        call_sessions[f"shift-{shift_id}-{idx}"] = {"shift_id": shift_id, "candidate": candidate, "ts": time.time()}
    except Exception as e:
        app.logger.error("Call to %s failed: %s", candidate["name"], e)
        call_next_employee(shift_id)

@app.route("/webhooks/sms", methods=["POST"])
def handle_sms():
    # Verify the Telnyx Ed25519 signature over the RAW body before trusting it.
    if not verify_telnyx_signature(request.get_data(), request.headers):
        return jsonify({"error": "invalid signature"}), 401
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    ep = event.get("payload", {})
    text = ep.get("text", "").strip().lower()
    sender = ep.get("from", {})
    if isinstance(sender, dict):
        sender = sender.get("phone_number", "")
    if "need" in text and ("closer" in text or "shift" in text or "cover" in text):
        shift_id = f"shift-{int(time.time())}"
        candidates = get_available_employees()
        shift_requests[shift_id] = {
            "id": shift_id, "manager_phone": sender, "description": text,
            "candidates": candidates, "current_idx": 0, "status": "calling", "ts": time.time()
        }
        ttl_cleanup(shift_requests)
        try:
            requests.post("https://api.telnyx.com/v2/messages", headers=HEADERS, timeout=10,
                          json={"from": TELNYX_PHONE, "to": sender,
                                "text": f"Got it. Calling {len(candidates)} available employees now."})
        except Exception as e:
            app.logger.error("Ack SMS failed: %s", e)
        if candidates:
            call_next_employee(shift_id)
    return jsonify({"status": "ok"})

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    # Verify the Telnyx Ed25519 signature over the RAW body before trusting it.
    if not verify_telnyx_signature(request.get_data(), request.headers):
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

    if event_type == "call.answered":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": "Hi, we need shift coverage tonight. Can you work the closing shift? Press 1 for yes, 2 for no.",
                            "voice": "female", "language": "en-US", "minimum_digits": 1, "maximum_digits": 1,
                            "client_state": encode_state({"step": "ask"})})

    elif event_type == "call.gather.ended":
        digits = ep.get("digits", "")
        session_key = None
        session = None
        for k, v in call_sessions.items():
            if k.startswith("shift-"):
                session_key = k
                session = v
                break
        if digits == "1" and session:
            shift_id = session.get("shift_id")
            shift = shift_requests.get(shift_id, {})
            candidate = session.get("candidate", {})
            shift["status"] = "filled"
            shift["filled_by"] = candidate.get("name")
            manager_phone = shift.get("manager_phone")
            if manager_phone:
                try:
                    requests.post("https://api.telnyx.com/v2/messages", headers=HEADERS, timeout=10,
                                  json={"from": TELNYX_PHONE, "to": manager_phone,
                                        "text": f"Shift covered! {candidate.get('name', '')} accepted."})
                    requests.post("https://api.telnyx.com/v2/messages", headers=HEADERS, timeout=10,
                                  json={"from": TELNYX_PHONE, "to": candidate.get("phone", ""),
                                        "text": "Confirmed! You are on the closing shift tonight. Thanks!"})
                except Exception as e:
                    app.logger.error("Confirmation SMS failed: %s", e)
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": "Great, you are confirmed. Check your texts for details. Thank you!",
                                "voice": "female", "language": "en-US"})
        else:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": "No problem. Have a good evening.", "voice": "female", "language": "en-US"})
            if session:
                shift_id = session.get("shift_id")
                call_next_employee(shift_id)

    elif event_type == "call.speak.ended":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
                      headers=HEADERS, timeout=10)

    elif event_type == "call.hangup":
        for k in list(call_sessions.keys()):
            if k.startswith("shift-"):
                del call_sessions[k]
                break

    return jsonify({"status": "ok"})

@app.route("/shifts", methods=["GET"])
def list_shifts():
    return jsonify({"shifts": list(shift_requests.values())})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-merge-shift-coverage"})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
