"""Merge Deal Desk Alerts — CRM webhook fires when a deal moves to negotiation
or exceeds a revenue threshold. Calls VP Sales with a spoken AI briefing that
includes deal size, stage, owner, and recent activity. VP can say "connect me"
to warm-transfer directly to the account executive."""
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
VP_SALES_NUMBER = os.getenv("VP_SALES_NUMBER")
DEAL_THRESHOLD = float(os.getenv("DEAL_THRESHOLD", "50000"))
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {
    "Authorization": f"Bearer {MERGE_API_KEY}",
    "X-Account-Token": MERGE_ACCOUNT_TOKEN or "",
    "Content-Type": "application/json",
}
MERGE_BASE = "https://api.merge.dev/api"

ALERT_STAGES = {"negotiation", "contract_sent", "verbal_commit", "closing"}

call_sessions = {}
alert_log = []
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
                            "You are a deal desk assistant briefing the VP of Sales. "
                            "Be concise and data-driven. Include deal name, amount, stage, "
                            "and what action is needed. Speak in 2-3 sentences max.\n\n"
                            f"Deal data: {json.dumps(context)}"
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
    return "A significant deal requires your attention. Please check your CRM."


def should_alert(deal):
    stage = (deal.get("stage") or deal.get("status") or "").lower().replace(" ", "_")
    amount = float(deal.get("amount") or 0)
    if stage in ALERT_STAGES:
        return True
    if amount >= DEAL_THRESHOLD:
        return True
    return False


@app.route("/webhooks/crm", methods=["POST"])
def handle_crm_webhook():
    """Merge CRM webhook — deal stage change triggers VP alert call."""
    data = request.get_json() or {}
    deal_id = data.get("id", "")
    deal = merge_get(f"/crm/v1/opportunities/{deal_id}") if deal_id else data
    if not deal:
        return jsonify({"error": "Deal not found"}), 404
    if not should_alert(deal):
        return jsonify({"status": "skipped", "reason": "Below threshold"})
    if not VP_SALES_NUMBER:
        return jsonify({"error": "VP_SALES_NUMBER not configured"}), 500
    deal_context = {
        "name": deal.get("name", "Unknown"),
        "amount": deal.get("amount"),
        "stage": deal.get("stage") or deal.get("status"),
        "close_date": deal.get("close_date"),
        "owner": deal.get("owner", {}).get("name", "Unassigned") if isinstance(deal.get("owner"), dict) else str(deal.get("owner", "Unassigned")),
        "account": deal.get("account", {}).get("name", "Unknown") if isinstance(deal.get("account"), dict) else str(deal.get("account", "Unknown")),
        "description": (deal.get("description") or "")[:200],
    }
    owner_phone = None
    owner = deal.get("owner", {})
    if isinstance(owner, dict):
        for pn in owner.get("phone_numbers", []):
            if pn.get("value"):
                owner_phone = pn["value"]
                break
    alert_id = f"alert-{int(time.time())}"
    call_sessions[alert_id] = {
        "deal": deal_context,
        "owner_phone": owner_phone,
        "ts": time.time(),
    }
    ttl_cleanup(call_sessions)
    alert_log.append({"id": alert_id, "deal": deal_context["name"], "amount": deal_context["amount"], "ts": time.time()})
    if len(alert_log) > MAX_ENTRIES:
        alert_log[:] = alert_log[-MAX_ENTRIES:]
    try:
        requests.post(
            "https://api.telnyx.com/v2/calls",
            headers=HEADERS,
            timeout=10,
            json={
                "connection_id": CONNECTION_ID,
                "to": VP_SALES_NUMBER,
                "from": TELNYX_PHONE,
                "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
                "client_state": encode_state({"alert_id": alert_id, "step": "briefing"}),
            },
        )
    except Exception as e:
        app.logger.error("VP call failed: %s", e)
        return jsonify({"error": "Failed to place alert call"}), 500
    return jsonify({"status": "alerting", "alert_id": alert_id, "deal": deal_context["name"]})


@app.route("/alert", methods=["POST"])
def manual_alert():
    """Manually trigger a deal alert for testing."""
    data = request.get_json() or {}
    deal_name = data.get("deal_name", "Test Deal")
    amount = data.get("amount", 100000)
    stage = data.get("stage", "negotiation")
    if not VP_SALES_NUMBER:
        return jsonify({"error": "VP_SALES_NUMBER not configured"}), 500
    alert_id = f"alert-{int(time.time())}"
    deal_context = {"name": deal_name, "amount": amount, "stage": stage}
    call_sessions[alert_id] = {"deal": deal_context, "ts": time.time()}
    ttl_cleanup(call_sessions)
    try:
        requests.post(
            "https://api.telnyx.com/v2/calls",
            headers=HEADERS,
            timeout=10,
            json={
                "connection_id": CONNECTION_ID,
                "to": VP_SALES_NUMBER,
                "from": TELNYX_PHONE,
                "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
                "client_state": encode_state({"alert_id": alert_id, "step": "briefing"}),
            },
        )
    except Exception as e:
        app.logger.error("Manual alert call failed: %s", e)
        return jsonify({"error": "Failed to place alert call"}), 500
    return jsonify({"status": "calling", "alert_id": alert_id})


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
    alert_id = state.get("alert_id", "")
    session = call_sessions.get(alert_id, {})
    deal = session.get("deal", {})

    if event_type == "call.answered":
        briefing = call_inference("Brief me on this deal.", deal)
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
            headers=HEADERS,
            timeout=10,
            json={
                "payload": f"Deal desk alert. {briefing} Say connect me to transfer to the rep, or hang up to dismiss.",
                "voice": "female",
                "language": "en-US",
                "input_type": "speech",
                "timeout_secs": 15,
                "client_state": encode_state({"alert_id": alert_id, "step": "awaiting_action"}),
            },
        )

    elif event_type == "call.gather.ended":
        speech = (ep.get("speech", {}).get("result", "") or "").lower()
        if "connect" in speech or "transfer" in speech:
            owner_phone = session.get("owner_phone")
            if owner_phone:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "Connecting you now.",
                        "voice": "female",
                        "language": "en-US",
                        "client_state": encode_state({"alert_id": alert_id, "step": "transferring", "target": owner_phone}),
                    },
                )
            else:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "No phone number on file for the deal owner. Please reach out directly. Goodbye.",
                        "voice": "female",
                        "language": "en-US",
                    },
                )
        else:
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": "Alert acknowledged. Goodbye.",
                    "voice": "female",
                    "language": "en-US",
                },
            )

    elif event_type == "call.speak.ended":
        if state.get("step") == "transferring":
            target = state.get("target")
            if target:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/transfer",
                    headers=HEADERS,
                    timeout=10,
                    json={"to": target},
                )
                return jsonify({"status": "ok"})
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
            headers=HEADERS,
            timeout=10,
        )

    elif event_type == "call.hangup":
        pass

    return jsonify({"status": "ok"})


@app.route("/deals", methods=["GET"])
def list_deals():
    """List recent deals from CRM."""
    result = merge_get("/crm/v1/opportunities", params={"page_size": 20})
    return jsonify(result or {"results": []})


@app.route("/alerts", methods=["GET"])
def list_alerts():
    """List recent alert history."""
    return jsonify({"alerts": alert_log[-50:]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-deal-desk-alerts", "pending_alerts": len(call_sessions)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
