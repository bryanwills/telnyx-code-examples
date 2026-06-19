"""Merge Ticket Escalation — critical ticket fires a webhook from Merge Ticketing.
App calls the on-call engineer with AI-generated context briefing (whisper).
Engineer says "connect me" to bridge with the customer who filed the ticket.
Logs escalation outcomes."""
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
ONCALL_NUMBER = os.getenv("ONCALL_NUMBER")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {
    "Authorization": f"Bearer {MERGE_API_KEY}",
    "X-Account-Token": MERGE_ACCOUNT_TOKEN or "",
    "Content-Type": "application/json",
}
MERGE_BASE = "https://api.merge.dev/api"
CRITICAL_PRIORITIES = {"CRITICAL", "URGENT", "HIGH"}

call_sessions = {}
escalation_log = []
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


def merge_patch(path, data):
    try:
        resp = requests.patch(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, json={"model": data}
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge PATCH %s failed: %s", path, e)
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
                            "You are an incident response assistant briefing an on-call "
                            "engineer. Be concise: what is broken, who reported it, severity, "
                            "and recommended first action. 2-3 sentences max.\n\n"
                            f"Ticket data: {json.dumps(context)}"
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
    return "A critical ticket needs your attention. Please check the ticket queue."


@app.route("/webhooks/ticket", methods=["POST"])
def handle_ticket_webhook():
    """Merge Ticketing webhook — critical ticket triggers on-call phone alert."""
    data = request.get_json() or {}
    ticket_id = data.get("id", "")
    ticket = merge_get(f"/ticketing/v1/tickets/{ticket_id}") if ticket_id else data
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    priority = (ticket.get("priority") or "").upper()
    if priority not in CRITICAL_PRIORITIES:
        return jsonify({"status": "skipped", "reason": f"Priority {priority} below threshold"})
    if not ONCALL_NUMBER:
        return jsonify({"error": "ONCALL_NUMBER not configured"}), 500
    ticket_context = {
        "subject": ticket.get("name", ticket.get("subject", "Unknown")),
        "priority": priority,
        "description": (ticket.get("description") or "")[:300],
        "creator": ticket.get("creator", {}).get("name", "Unknown") if isinstance(ticket.get("creator"), dict) else str(ticket.get("creator", "Unknown")),
        "ticket_id": ticket_id,
        "created_at": ticket.get("created_at", ""),
    }
    reporter_phone = None
    creator = ticket.get("creator") or ticket.get("contact")
    if isinstance(creator, dict):
        for pn in creator.get("phone_numbers", []):
            if pn.get("value") or pn.get("number"):
                reporter_phone = pn.get("value") or pn.get("number")
                break
    esc_id = f"esc-{int(time.time())}"
    call_sessions[esc_id] = {
        "ticket": ticket_context,
        "reporter_phone": reporter_phone,
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
                "to": ONCALL_NUMBER,
                "from": TELNYX_PHONE,
                "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
                "client_state": encode_state({"esc_id": esc_id}),
            },
        )
    except Exception as e:
        app.logger.error("On-call phone alert failed: %s", e)
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "escalating", "esc_id": esc_id, "ticket": ticket_context["subject"]})


@app.route("/escalate", methods=["POST"])
def manual_escalate():
    """Manually trigger an escalation for testing."""
    data = request.get_json() or {}
    subject = data.get("subject", "Test Critical Ticket")
    description = data.get("description", "Production database connection failures.")
    if not ONCALL_NUMBER:
        return jsonify({"error": "ONCALL_NUMBER not configured"}), 500
    esc_id = f"esc-{int(time.time())}"
    ticket_context = {"subject": subject, "priority": "CRITICAL", "description": description}
    call_sessions[esc_id] = {"ticket": ticket_context, "outcome": "pending", "ts": time.time()}
    ttl_cleanup(call_sessions)
    try:
        requests.post(
            "https://api.telnyx.com/v2/calls",
            headers=HEADERS,
            timeout=10,
            json={
                "connection_id": CONNECTION_ID,
                "to": ONCALL_NUMBER,
                "from": TELNYX_PHONE,
                "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice",
                "client_state": encode_state({"esc_id": esc_id}),
            },
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "calling", "esc_id": esc_id})


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
    esc_id = state.get("esc_id", "")
    session = call_sessions.get(esc_id, {})
    ticket = session.get("ticket", {})

    if event_type == "call.answered":
        briefing = call_inference("Brief me on this incident.", ticket)
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
            headers=HEADERS,
            timeout=10,
            json={
                "payload": (
                    f"Critical ticket alert. {briefing} "
                    f"Say connect me to bridge with the reporter, or acknowledge to dismiss."
                ),
                "voice": "female",
                "language": "en-US",
                "input_type": "speech",
                "timeout_secs": 15,
                "client_state": encode_state({"esc_id": esc_id, "step": "awaiting"}),
            },
        )

    elif event_type == "call.gather.ended":
        speech = (ep.get("speech", {}).get("result", "") or "").lower()
        if "connect" in speech or "bridge" in speech:
            reporter_phone = session.get("reporter_phone")
            if reporter_phone:
                session["outcome"] = "connected"
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "Connecting you to the reporter now.",
                        "voice": "female",
                        "language": "en-US",
                        "client_state": encode_state({"esc_id": esc_id, "step": "transferring", "target": reporter_phone}),
                    },
                )
            else:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "No phone number on file for the reporter. Check the ticket for contact details. Goodbye.",
                        "voice": "female",
                        "language": "en-US",
                    },
                )
        else:
            session["outcome"] = "acknowledged"
            ticket_id = ticket.get("ticket_id")
            if ticket_id:
                merge_patch(f"/ticketing/v1/tickets/{ticket_id}", {"status": "IN_PROGRESS"})
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": "Acknowledged. Ticket marked in progress. Good luck.",
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
        if session:
            escalation_log.append({
                "esc_id": esc_id,
                "ticket": ticket.get("subject"),
                "priority": ticket.get("priority"),
                "outcome": session.get("outcome", "no_answer"),
                "ts": time.time(),
            })
            if len(escalation_log) > MAX_ENTRIES:
                escalation_log[:] = escalation_log[-MAX_ENTRIES:]

    return jsonify({"status": "ok"})


@app.route("/tickets", methods=["GET"])
def list_tickets():
    """List critical tickets from Merge Ticketing."""
    result = merge_get("/ticketing/v1/tickets", params={"priority": "URGENT", "page_size": 20})
    return jsonify(result or {"results": []})


@app.route("/escalations", methods=["GET"])
def list_escalations():
    """List escalation history."""
    return jsonify({"escalations": escalation_log[-50:]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-ticket-escalation", "pending": len(call_sessions)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
