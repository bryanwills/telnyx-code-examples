"""Merge Expense by Phone — salesperson calls, dictates an expense. AI extracts
amount, merchant, category, and deal context. Creates entry in accounting via
Merge. Tags to CRM opportunity if mentioned. Sends SMS receipt with details."""
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
TELNYX_PHONE = os.getenv("TELNYX_PHONE_NUMBER")
CONNECTION_ID = os.getenv("TELNYX_CONNECTION_ID", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
MERGE_API_KEY = os.getenv("MERGE_API_KEY")
MERGE_ACCOUNT_TOKEN = os.getenv("MERGE_ACCOUNT_TOKEN")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {
    "Authorization": f"Bearer {MERGE_API_KEY}",
    "X-Account-Token": MERGE_ACCOUNT_TOKEN or "",
    "Content-Type": "application/json",
}
MERGE_BASE = "https://api.merge.dev/api"

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


call_sessions = {}
expense_log = []
MAX_ENTRIES = 10000


def ttl_cleanup(store, max_size=MAX_ENTRIES):
    if len(store) > max_size:
        oldest = sorted(store, key=lambda k: store[k].get("ts", 0))
        for k in oldest[: len(store) - max_size]:
            del store[k]


def encode_state(data):
    return base64.b64encode(json.dumps(data).encode()).decode()


def decode_state(b64):
    try:
        return json.loads(base64.b64decode(b64).decode())
    except Exception:
        return {}


def merge_get(path, params=None):
    try:
        resp = requests.get(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, params=params
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge GET %s failed: %s", path, e)
    return None


def merge_post(path, data):
    try:
        resp = requests.post(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, json={"model": data}
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge POST %s failed: %s", path, e)
    return None


def extract_expense(speech):
    """Use AI to extract structured expense data from spoken description."""
    try:
        resp = requests.post(
            INFERENCE_URL,
            headers=HEADERS,
            timeout=15,
            json={
                "model": AI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Extract expense details from the spoken description. Return JSON: "
                            '{"amount": number, "merchant": "string", "category": "meals|travel|office|entertainment|other", '
                            '"description": "brief description", "deal_name": "string or null if no deal mentioned"}'
                        ),
                    },
                    {"role": "user", "content": speech},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        if resp.ok:
            return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        app.logger.error("Expense extraction failed: %s", e)
    return None


def call_inference(prompt, context):
    try:
        resp = requests.post(
            INFERENCE_URL,
            headers=HEADERS,
            timeout=15,
            json={
                "model": AI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expense logging assistant. Confirm the expense details "
                            "back to the user. Be concise — 1-2 sentences.\n\n"
                            f"Expense data: {json.dumps(context)}"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        app.logger.error("Inference failed: %s", e)
    return "I have recorded your expense."


def find_deal(deal_name):
    """Search CRM for matching opportunity."""
    if not deal_name:
        return None
    result = merge_get("/crm/v1/opportunities", params={"name": deal_name, "page_size": 5})
    if result and result.get("results"):
        return result["results"][0]
    return None


def send_receipt(phone, expense_data):
    """Send SMS receipt."""
    amount = expense_data.get("amount", 0)
    merchant = expense_data.get("merchant", "Unknown")
    category = expense_data.get("category", "other")
    try:
        requests.post(
            "https://api.telnyx.com/v2/messages",
            headers=HEADERS,
            timeout=10,
            json={
                "from": TELNYX_PHONE,
                "to": phone,
                "text": (
                    f"Expense logged: ${amount:.2f} at {merchant} ({category}). "
                    f"Ref: EXP-{int(time.time()) % 100000}"
                ),
            },
        )
        return True
    except Exception as e:
        app.logger.error("Receipt SMS failed: %s", e)
        return False


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

    state = decode_state(ep.get("client_state", ""))

    if event_type == "call.initiated" and ep.get("direction") == "incoming":
        caller = ep.get("from", "")
        call_sessions[cc_id] = {"caller": caller, "ts": time.time()}
        ttl_cleanup(call_sessions)
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
            headers=HEADERS,
            timeout=10,
            json={"client_state": encode_state({"step": "greeting"})},
        )

    elif event_type == "call.answered":
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
            headers=HEADERS,
            timeout=10,
            json={
                "payload": (
                    "Expense logger. Tell me what you spent, how much, where, "
                    "and what client or deal it was for."
                ),
                "voice": "female",
                "language": "en-US",
                "input_type": "speech",
                "timeout_secs": 60,
                "client_state": encode_state({"step": "capture"}),
            },
        )

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        step = state.get("step", "capture")
        session = call_sessions.get(cc_id, {})

        if step == "capture" and speech:
            expense_data = extract_expense(speech)
            if expense_data and expense_data.get("amount"):
                session["expense"] = expense_data
                # Create expense in accounting
                merge_post("/accounting/v1/expenses", {
                    "total_amount": expense_data.get("amount"),
                    "memo": expense_data.get("description", ""),
                    "transaction_date": time.strftime("%Y-%m-%d"),
                })
                # Tag to deal if mentioned
                deal_name = expense_data.get("deal_name")
                if deal_name:
                    deal = find_deal(deal_name)
                    if deal:
                        session["linked_deal"] = deal.get("name")
                confirmation = call_inference("Confirm this expense.", expense_data)
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": f"{confirmation} Would you like to log another expense?",
                        "voice": "female",
                        "language": "en-US",
                        "input_type": "speech",
                        "timeout_secs": 15,
                        "client_state": encode_state({"step": "another"}),
                    },
                )
                # Send receipt
                caller = session.get("caller")
                if caller and TELNYX_PHONE:
                    send_receipt(caller, expense_data)
                # Log
                expense_log.append({**expense_data, "caller": caller, "ts": time.time()})
                if len(expense_log) > MAX_ENTRIES:
                    expense_log[:] = expense_log[-MAX_ENTRIES:]
            else:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "I could not extract the expense details. Please try again: how much, where, and for what?",
                        "voice": "female",
                        "language": "en-US",
                        "input_type": "speech",
                        "timeout_secs": 60,
                        "client_state": encode_state({"step": "capture"}),
                    },
                )

        elif step == "another" and speech:
            if "yes" in speech.lower() or "another" in speech.lower():
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "Go ahead. What did you spend?",
                        "voice": "female",
                        "language": "en-US",
                        "input_type": "speech",
                        "timeout_secs": 60,
                        "client_state": encode_state({"step": "capture"}),
                    },
                )
            else:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "All done. Check your texts for receipts. Goodbye.",
                        "voice": "female",
                        "language": "en-US",
                    },
                )

    elif event_type == "call.speak.ended":
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
            headers=HEADERS,
            timeout=10,
        )

    elif event_type == "call.hangup":
        call_sessions.pop(cc_id, None)

    return jsonify({"status": "ok"})


@app.route("/expenses", methods=["GET"])
def list_expenses():
    """List logged expenses."""
    return jsonify({"expenses": expense_log[-50:]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-expense-by-phone", "total_logged": len(expense_log)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
