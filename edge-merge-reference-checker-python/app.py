"""Edge Merge Reference Checker — ATS application reaches reference-check stage.
Calls each reference. AI conducts structured interview with scored questions.
Updates ATS with results. SMS summary to hiring manager."""
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
HIRING_MANAGER_PHONE = os.getenv("HIRING_MANAGER_PHONE", "")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {"Authorization": f"Bearer {MERGE_API_KEY}", "X-Account-Token": MERGE_ACCOUNT_TOKEN or "", "Content-Type": "application/json"}
MERGE_BASE = "https://api.merge.dev/api"

def verify_telnyx_signature(body: bytes, headers: dict, tolerance: int = 300) -> bool:
    """Verify the Telnyx Ed25519 signature over "<telnyx-timestamp>|<raw body>".

    Telnyx signs every webhook (telnyx-signature-ed25519 / telnyx-timestamp headers).
    This app uses raw requests rather than the Telnyx SDK, so verify directly with the
    public key (Portal > Keys & Credentials > Public Key). Reject >5 min skew (replay).
    """
    sig_b64 = headers.get("telnyx-signature-ed25519", "")
    timestamp = headers.get("telnyx-timestamp", "")
    if not (sig_b64 and timestamp and TELNYX_PUBLIC_KEY):
        return False
    try:
        if abs(time.time() - int(timestamp)) > tolerance:
            return False
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(TELNYX_PUBLIC_KEY))
        public_key.verify(base64.b64decode(sig_b64), f"{timestamp}|".encode() + body)
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


QUESTIONS = [
    "How long did you work with the candidate and in what capacity?",
    "What were their greatest strengths in the role?",
    "Can you describe a challenging situation they handled well?",
    "On a scale of 1 to 5, how strongly would you recommend them for a similar role?",
    "Is there anything else you think we should know?"
]

call_sessions = {}
reference_reports = {}
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

def merge_patch(path, data):
    try:
        resp = requests.patch(f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, json={"model": data})
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge PATCH %s failed: %s", path, e)
    return None

def score_reference(answers):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": "Score this reference check. Respond with JSON: {\"overall_score\": 1-5, \"strengths\": [list], \"concerns\": [list], \"recommendation\": \"strong yes|yes|neutral|no|strong no\", \"summary\": \"2 sentence summary\"}"},
                {"role": "user", "content": json.dumps(answers)}
            ],
            "response_format": {"type": "json_object"}
        })
        if resp.ok:
            return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        app.logger.error("Scoring failed: %s", e)
    return {"overall_score": 3, "summary": "Unable to score automatically."}

@app.route("/check", methods=["POST"])
def start_reference_check():
    data = request.get_json() or {}
    candidate_name = data.get("candidate_name", "the candidate")
    references = data.get("references", [])
    application_id = data.get("application_id", "")
    if not references:
        return jsonify({"error": "references array required (each with name and phone)"}), 400
    check_id = f"ref-{int(time.time())}"
    reference_reports[check_id] = {
        "id": check_id, "candidate": candidate_name, "application_id": application_id,
        "references": [], "status": "in_progress", "ts": time.time()
    }
    for ref in references:
        phone = ref.get("phone")
        if not phone:
            continue
        ref_id = f"{check_id}-{len(reference_reports[check_id]['references'])}"
        call_sessions[ref_id] = {
            "check_id": check_id, "reference_name": ref.get("name", ""),
            "candidate": candidate_name, "question_idx": 0, "answers": [], "ts": time.time()
        }
        ttl_cleanup(call_sessions)
        try:
            requests.post("https://api.telnyx.com/v2/calls", headers=HEADERS, timeout=10, json={
                "connection_id": CONNECTION_ID, "to": phone, "from": TELNYX_PHONE,
                "webhook_url": request.url_root.rstrip("/") + "/webhooks/voice"
            })
        except Exception as e:
            app.logger.error("Reference call to %s failed: %s", phone, e)
    return jsonify({"status": "calling", "check_id": check_id, "references": len(references)})

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    # Verify the Telnyx Ed25519 signature against the RAW body before trusting anything.
    raw_body = request.get_data()
    # request.headers is case-insensitive (Werkzeug); dict() would Title-case keys
    # and break the lowercase header lookups in verify_telnyx_signature.
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

    if event_type == "call.answered":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": f"Hello, this is an automated reference check call. I have a few questions. {QUESTIONS[0]}",
                            "voice": "female", "language": "en-US", "input_type": "speech", "timeout_secs": 60,
                            "client_state": encode_state({"step": "question", "q_idx": 0})})

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        state = decode_state(ep.get("client_state", ""))
        q_idx = state.get("q_idx", 0)
        session = None
        for k, v in call_sessions.items():
            if k.startswith("ref-"):
                session = v
                session_key = k
                break
        if session and speech:
            session["answers"].append({"question": QUESTIONS[q_idx], "answer": speech})
            next_idx = q_idx + 1
            if next_idx < len(QUESTIONS):
                requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                              headers=HEADERS, timeout=10,
                              json={"payload": QUESTIONS[next_idx], "voice": "female", "language": "en-US",
                                    "input_type": "speech", "timeout_secs": 60,
                                    "client_state": encode_state({"step": "question", "q_idx": next_idx})})
            else:
                scored = score_reference(session["answers"])
                check_id = session.get("check_id")
                report = reference_reports.get(check_id, {})
                report.setdefault("references", []).append({
                    "name": session.get("reference_name"), "answers": session["answers"], "score": scored
                })
                if len(report["references"]) >= len([s for s in call_sessions.values() if s.get("check_id") == check_id]):
                    report["status"] = "complete"
                    if HIRING_MANAGER_PHONE:
                        avg_score = sum(r.get("score", {}).get("overall_score", 3) for r in report["references"]) / max(len(report["references"]), 1)
                        try:
                            requests.post("https://api.telnyx.com/v2/messages", headers=HEADERS, timeout=10,
                                          json={"from": TELNYX_PHONE, "to": HIRING_MANAGER_PHONE,
                                                "text": f"Reference check complete for {report.get('candidate', '')}. Avg score: {avg_score:.1f}/5. {len(report['references'])} references checked."})
                        except Exception as e:
                            app.logger.error("Summary SMS failed: %s", e)
                    if report.get("application_id"):
                        merge_patch(f"/ats/v1/applications/{report['application_id']}", {"current_stage": "reference_complete"})
                requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                              headers=HEADERS, timeout=10,
                              json={"payload": "Thank you for your time. Your responses have been recorded. Goodbye.",
                                    "voice": "female", "language": "en-US"})

    elif event_type == "call.speak.ended":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
                      headers=HEADERS, timeout=10)

    elif event_type == "call.hangup":
        for k in list(call_sessions.keys()):
            if k.startswith("ref-"):
                del call_sessions[k]
                break

    return jsonify({"status": "ok"})

@app.route("/reports", methods=["GET"])
def list_reports():
    return jsonify({"reports": list(reference_reports.values())})

@app.route("/reports/<check_id>", methods=["GET"])
def get_report(check_id):
    report = reference_reports.get(check_id)
    if not report:
        return jsonify({"error": "Not found"}), 404
    return jsonify(report)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-merge-reference-checker"})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
