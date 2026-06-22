"""Merge Pipeline Briefing — morning pipeline briefing system. Pulls each reps
pipeline from CRM via Merge. AI generates a spoken briefing covering total deals,
value, deals closing this week, and stale opportunities. Calls each rep with
their personalized briefing."""
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
STALE_DAYS = int(os.getenv("STALE_DAYS", "7"))
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {
    "Authorization": f"Bearer {MERGE_API_KEY}",
    "X-Account-Token": MERGE_ACCOUNT_TOKEN or "",
    "Content-Type": "application/json",
}
MERGE_BASE = "https://api.merge.dev/api"

call_sessions = {}
briefing_log = []
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


def build_pipeline_summary(deals):
    """Analyze deals and build pipeline summary."""
    today = time.strftime("%Y-%m-%d")
    week_from_now = time.strftime("%Y-%m-%d", time.localtime(time.time() + 7 * 86400))
    stale_cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - STALE_DAYS * 86400))
    total_value = sum(float(d.get("amount") or 0) for d in deals)
    closing_soon = [
        d for d in deals
        if d.get("close_date") and today <= d["close_date"][:10] <= week_from_now
    ]
    stale = []
    for d in deals:
        last_activity = d.get("last_activity_at") or d.get("modified_at") or ""
        if last_activity and last_activity[:10] < stale_cutoff:
            stale.append(d)
    top_deals = sorted(deals, key=lambda x: float(x.get("amount") or 0), reverse=True)[:5]
    return {
        "total_deals": len(deals),
        "total_value": total_value,
        "closing_this_week": len(closing_soon),
        "closing_value": sum(float(d.get("amount") or 0) for d in closing_soon),
        "stale_deals": len(stale),
        "top_deals": [{"name": d.get("name"), "amount": d.get("amount"), "stage": d.get("stage")} for d in top_deals],
    }


def generate_briefing(summary):
    """Use AI to generate spoken pipeline briefing."""
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
                            "You are a sales intelligence assistant delivering a morning "
                            "pipeline briefing by phone. Be concise, data-driven, and "
                            "actionable. Mention total pipeline value, deals closing this "
                            "week, stale deals, and top opportunities. Keep it under 45 "
                            "seconds of speaking time. No markdown or formatting."
                        ),
                    },
                    {"role": "user", "content": f"Pipeline data: {json.dumps(summary)}"},
                ],
            },
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        app.logger.error("Briefing generation failed: %s", e)
    return (
        f"You have {summary['total_deals']} deals worth "
        f"${summary['total_value']:,.0f} total. "
        f"{summary['closing_this_week']} closing this week. "
        f"{summary['stale_deals']} stale deals need attention."
    )


@app.route("/briefing", methods=["POST"])
def trigger_briefing():
    """Trigger a pipeline briefing call."""
    data = request.get_json() or {}
    phone = data.get("phone")
    rep_name = data.get("rep_name", "")
    owner_id = data.get("owner_id")
    if not phone:
        return jsonify({"error": "phone required"}), 400
    # Pull pipeline from CRM
    params = {"page_size": 100}
    if owner_id:
        params["owner_id"] = owner_id
    pipeline = merge_get("/crm/v1/opportunities", params=params)
    deals = (pipeline or {}).get("results", [])
    summary = build_pipeline_summary(deals)
    briefing_text = generate_briefing(summary)
    brief_id = f"brief-{int(time.time())}"
    call_sessions[brief_id] = {
        "rep_name": rep_name,
        "phone": phone,
        "summary": summary,
        "briefing_text": briefing_text,
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
                "client_state": encode_state({"brief_id": brief_id}),
            },
        )
    except Exception as e:
        app.logger.error("Briefing call failed: %s", e)
        return jsonify({"error": "briefing call failed"}), 500
    return jsonify({"status": "calling", "brief_id": brief_id, "pipeline": summary})


@app.route("/briefing/preview", methods=["POST"])
def preview_briefing():
    """Preview briefing without calling — returns text and summary."""
    data = request.get_json() or {}
    owner_id = data.get("owner_id")
    params = {"page_size": 100}
    if owner_id:
        params["owner_id"] = owner_id
    pipeline = merge_get("/crm/v1/opportunities", params=params)
    deals = (pipeline or {}).get("results", [])
    summary = build_pipeline_summary(deals)
    briefing_text = generate_briefing(summary)
    return jsonify({"summary": summary, "briefing_text": briefing_text})


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
    brief_id = state.get("brief_id", "")
    session = call_sessions.get(brief_id, {})

    if event_type == "call.answered":
        rep = session.get("rep_name", "")
        greeting = f"Good morning{' ' + rep if rep else ''}. Here is your pipeline briefing. "
        briefing = session.get("briefing_text", "No pipeline data available.")
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
            headers=HEADERS,
            timeout=10,
            json={
                "payload": greeting + briefing + " Would you like me to repeat any part?",
                "voice": "female",
                "language": "en-US",
                "input_type": "speech",
                "timeout_secs": 15,
                "client_state": encode_state({"brief_id": brief_id, "step": "followup"}),
            },
        )

    elif event_type == "call.gather.ended":
        speech = (ep.get("speech", {}).get("result", "") or "").lower()
        if "repeat" in speech or "again" in speech:
            briefing = session.get("briefing_text", "")
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": briefing + " Anything else?",
                    "voice": "female",
                    "language": "en-US",
                    "input_type": "speech",
                    "timeout_secs": 15,
                    "client_state": encode_state({"brief_id": brief_id, "step": "followup"}),
                },
            )
        elif "stale" in speech or "attention" in speech:
            summary = session.get("summary", {})
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": f"You have {summary.get('stale_deals', 0)} deals with no activity in {STALE_DAYS} days. Check your CRM for details. Have a great day.",
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
                    "payload": "Good luck today. Go close some deals.",
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
        if session:
            briefing_log.append({
                "brief_id": brief_id,
                "rep": session.get("rep_name"),
                "deals": session.get("summary", {}).get("total_deals"),
                "value": session.get("summary", {}).get("total_value"),
                "ts": time.time(),
            })
            if len(briefing_log) > MAX_ENTRIES:
                briefing_log[:] = briefing_log[-MAX_ENTRIES:]

    return jsonify({"status": "ok"})


@app.route("/briefings", methods=["GET"])
def list_briefings():
    """List briefing history."""
    return jsonify({"briefings": briefing_log[-50:]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-pipeline-briefing", "total_briefings": len(briefing_log)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
