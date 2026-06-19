"""Merge Invoice Collector — pulls overdue invoices from accounting via Merge.
AI calls debtors in priority order (largest first). Negotiates payment terms
conversationally. Sends SMS payment link mid-call. Logs outcomes."""
import os, json, time, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

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
PAYMENT_URL_BASE = os.getenv("PAYMENT_URL_BASE", "https://pay.example.com/invoice")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {
    "Authorization": f"Bearer {MERGE_API_KEY}",
    "X-Account-Token": MERGE_ACCOUNT_TOKEN or "",
    "Content-Type": "application/json",
}
MERGE_BASE = "https://api.merge.dev/api"

call_sessions = {}
collection_log = []
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
                            "You are a professional accounts receivable agent. Be firm but "
                            "polite. Offer payment plan options when asked. Keep responses "
                            "under 2 sentences. Never threaten — focus on resolution.\n\n"
                            f"Invoice data: {json.dumps(context)}"
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
    return "I can help resolve this balance. Would you like to discuss payment options?"


def send_payment_link(phone, invoice_number, amount):
    """Send SMS with payment link."""
    pay_url = f"{PAYMENT_URL_BASE}/{invoice_number}"
    try:
        requests.post(
            "https://api.telnyx.com/v2/messages",
            headers=HEADERS,
            timeout=10,
            json={
                "from": TELNYX_PHONE,
                "to": phone,
                "text": f"Pay invoice {invoice_number} (${amount:.2f}): {pay_url}",
            },
        )
        return True
    except Exception as e:
        app.logger.error("Payment SMS failed: %s", e)
        return False


@app.route("/collect", methods=["POST"])
def start_collection():
    """Pull overdue invoices from Merge Accounting and start calling."""
    result = merge_get("/accounting/v1/invoices", params={"status": "OVERDUE", "page_size": 50})
    if not result:
        return jsonify({"error": "Failed to fetch invoices"}), 500
    invoices = result.get("results", [])
    sorted_inv = sorted(
        invoices,
        key=lambda x: float(x.get("total_amount") or x.get("amount") or 0),
        reverse=True,
    )
    limit = int(request.args.get("limit", 5))
    called = 0
    skipped = 0
    for inv in sorted_inv[:limit]:
        inv_id = inv.get("id", "")
        inv_number = inv.get("number", inv_id[:8])
        amount = float(inv.get("total_amount") or inv.get("amount") or 0)
        contact = inv.get("contact", {})
        phone = None
        if isinstance(contact, dict):
            for pn in contact.get("phone_numbers", []):
                if pn.get("number") or pn.get("value"):
                    phone = pn.get("number") or pn.get("value")
                    break
        if not phone:
            skipped += 1
            continue
        session_id = f"collect-{inv_id[:12]}"
        call_sessions[session_id] = {
            "invoice_id": inv_id,
            "invoice_number": inv_number,
            "amount": amount,
            "due_date": inv.get("due_date"),
            "phone": phone,
            "contact_name": contact.get("name", "Customer") if isinstance(contact, dict) else "Customer",
            "history": [],
            "outcome": "pending",
            "ts": time.time(),
        }
        ttl_cleanup(call_sessions)
        try:
            requests.post(
                "https://api.telnyx.com/v2/calls",
                headers=HEADERS,
                timeout=10,
                json={
                    "connection_id": CONNECTION_ID,
                    "to": phone,
                    "from": TELNYX_PHONE,
                    "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
                    "client_state": encode_state({"session_id": session_id}),
                },
            )
            called += 1
        except Exception as e:
            app.logger.error("Collection call to %s failed: %s", phone, e)
    return jsonify({"status": "collecting", "overdue_total": len(invoices), "calling": called, "skipped_no_phone": skipped})


@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    ep = event.get("payload", {})
    cc_id = ep.get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    state = decode_state(ep.get("client_state", ""))
    session_id = state.get("session_id", "")
    session = call_sessions.get(session_id, {})

    if event_type == "call.answered":
        name = session.get("contact_name", "")
        amount = session.get("amount", 0)
        inv_num = session.get("invoice_number", "")
        greeting = (
            f"Hello {name}, this is a courtesy call regarding invoice {inv_num} "
            f"for ${amount:.2f} which is past due. I would like to help you resolve this today. "
            f"Would you like to pay now, or discuss a payment plan?"
        )
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
            headers=HEADERS,
            timeout=10,
            json={
                "payload": greeting,
                "voice": "female",
                "language": "en-US",
                "input_type": "speech",
                "timeout_secs": 30,
                "client_state": encode_state({"session_id": session_id, "step": "negotiation"}),
            },
        )

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        if speech and session:
            session.setdefault("history", []).append({"role": "customer", "text": speech})
            lower = speech.lower()
            if "pay now" in lower or "send" in lower or "link" in lower:
                phone = session.get("phone")
                inv_num = session.get("invoice_number", "")
                amount = session.get("amount", 0)
                sent = send_payment_link(phone, inv_num, amount) if phone else False
                if sent:
                    response = "I just sent a payment link to your phone. You can complete the payment there. Is there anything else?"
                else:
                    response = "I was unable to send the link. Please visit our website to make a payment. Is there anything else?"
                session["outcome"] = "payment_link_sent"
            else:
                inv_data = {
                    "invoice": session.get("invoice_number"),
                    "amount": session.get("amount"),
                    "due_date": session.get("due_date"),
                }
                response = call_inference(speech, inv_data)
            session["history"].append({"role": "agent", "text": response})
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": response,
                    "voice": "female",
                    "language": "en-US",
                    "input_type": "speech",
                    "timeout_secs": 30,
                    "client_state": encode_state({"session_id": session_id, "step": "negotiation"}),
                },
            )
        else:
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": "Thank you for your time. Please reach out if you have questions about your balance. Goodbye.",
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
        if session and session.get("outcome") == "pending":
            session["outcome"] = "completed_no_payment"
        if session:
            collection_log.append({
                "session_id": session_id,
                "invoice": session.get("invoice_number"),
                "amount": session.get("amount"),
                "outcome": session.get("outcome"),
                "turns": len(session.get("history", [])),
                "ts": time.time(),
            })
            if len(collection_log) > MAX_ENTRIES:
                collection_log[:] = collection_log[-MAX_ENTRIES:]

    return jsonify({"status": "ok"})


@app.route("/invoices", methods=["GET"])
def list_invoices():
    """List overdue invoices from Merge Accounting."""
    result = merge_get("/accounting/v1/invoices", params={"status": "OVERDUE", "page_size": 20})
    return jsonify(result or {"results": []})


@app.route("/collections", methods=["GET"])
def list_collections():
    """List collection call outcomes."""
    return jsonify({"collections": collection_log[-50:]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-invoice-collector", "active_calls": len(call_sessions)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
