"""Merge Recruitment Hotline — job seekers call. AI asks what role they want,
pulls matching open positions from ATS via Merge, describes top matches
conversationally, and submits applications on the callers behalf."""
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

call_sessions = {}
application_log = []
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


def search_jobs(query):
    """Search open jobs in ATS."""
    result = merge_get("/ats/v1/jobs", params={"status": "OPEN", "page_size": 20})
    if not result:
        return []
    jobs = result.get("results", [])
    if not query:
        return jobs[:5]
    query_lower = query.lower()
    scored = []
    for job in jobs:
        name = (job.get("name") or "").lower()
        dept = ""
        if isinstance(job.get("departments"), list):
            dept = " ".join(str(d.get("name", "")) for d in job["departments"] if isinstance(d, dict)).lower()
        score = 0
        for word in query_lower.split():
            if word in name:
                score += 2
            if word in dept:
                score += 1
        if score > 0:
            scored.append((score, job))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [j for _, j in scored[:5]] if scored else jobs[:3]


def describe_jobs(jobs):
    """Use AI to create spoken description of matching jobs."""
    job_list = []
    for i, j in enumerate(jobs, 1):
        name = j.get("name", "Untitled")
        dept = ""
        if isinstance(j.get("departments"), list) and j["departments"]:
            d = j["departments"][0]
            dept = d.get("name", "") if isinstance(d, dict) else str(d)
        loc = ""
        if isinstance(j.get("offices"), list) and j["offices"]:
            o = j["offices"][0]
            loc = o.get("name", "") if isinstance(o, dict) else str(o)
        job_list.append(f"{i}. {name}" + (f" in {dept}" if dept else "") + (f", {loc}" if loc else ""))
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
                            "You are a recruitment assistant on a phone call. Briefly describe "
                            "these open positions to the caller. Be conversational. List by "
                            "number so they can pick one. Keep it under 30 seconds of speaking."
                        ),
                    },
                    {"role": "user", "content": "\n".join(job_list)},
                ],
            },
        )
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        app.logger.error("Job description failed: %s", e)
    return ". ".join(job_list)


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
                "payload": "Welcome to our recruitment hotline. What type of role are you looking for?",
                "voice": "female",
                "language": "en-US",
                "input_type": "speech",
                "timeout_secs": 30,
                "client_state": encode_state({"step": "search"}),
            },
        )

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        step = state.get("step", "")
        session = call_sessions.get(cc_id, {})

        if step == "search" and speech:
            jobs = search_jobs(speech)
            if not jobs:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "I could not find matching positions right now. Would you like to try a different search?",
                        "voice": "female",
                        "language": "en-US",
                        "input_type": "speech",
                        "timeout_secs": 15,
                        "client_state": encode_state({"step": "search"}),
                    },
                )
            else:
                session["matching_jobs"] = jobs
                description = describe_jobs(jobs)
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": f"{description} Which number interests you? Or say none to end.",
                        "voice": "female",
                        "language": "en-US",
                        "input_type": "speech",
                        "timeout_secs": 20,
                        "client_state": encode_state({"step": "select"}),
                    },
                )

        elif step == "select" and speech:
            lower = speech.lower()
            if "none" in lower or "no" in lower:
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "No problem. Check our careers page for new openings. Thank you for calling. Goodbye.",
                        "voice": "female",
                        "language": "en-US",
                    },
                )
            else:
                # Try to extract number
                jobs = session.get("matching_jobs", [])
                selected_idx = None
                for i in range(1, len(jobs) + 1):
                    if str(i) in speech or ["one", "two", "three", "four", "five"][i - 1] in lower:
                        selected_idx = i - 1
                        break
                if selected_idx is not None and selected_idx < len(jobs):
                    selected_job = jobs[selected_idx]
                    session["selected_job"] = selected_job
                    requests.post(
                        f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                        headers=HEADERS,
                        timeout=10,
                        json={
                            "payload": f"Great choice. I can submit your application for {selected_job.get('name', 'that role')}. Please tell me your full name.",
                            "voice": "female",
                            "language": "en-US",
                            "input_type": "speech",
                            "timeout_secs": 15,
                            "client_state": encode_state({"step": "get_name", "job_id": selected_job.get("id")}),
                        },
                    )
                else:
                    requests.post(
                        f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                        headers=HEADERS,
                        timeout=10,
                        json={
                            "payload": "I did not catch which position. Could you say the number?",
                            "voice": "female",
                            "language": "en-US",
                            "input_type": "speech",
                            "timeout_secs": 15,
                            "client_state": encode_state({"step": "select"}),
                        },
                    )

        elif step == "get_name" and speech:
            parts = speech.strip().split()
            first_name = parts[0] if parts else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            caller = session.get("caller", "")
            job_id = state.get("job_id")
            # Create candidate in ATS
            candidate = merge_post("/ats/v1/candidates", {
                "first_name": first_name,
                "last_name": last_name,
                "phone_numbers": [{"value": caller, "phone_number_type": "MOBILE"}],
            })
            cand_id = None
            if candidate:
                cand_id = candidate.get("model", {}).get("id")
            # Submit application
            if cand_id and job_id:
                app_result = merge_post("/ats/v1/applications", {
                    "candidate": cand_id,
                    "job": job_id,
                    "source": "Phone Hotline",
                })
                if app_result:
                    application_log.append({
                        "candidate": f"{first_name} {last_name}".strip(),
                        "job_id": job_id,
                        "phone": caller,
                        "ts": time.time(),
                    })
                    if len(application_log) > MAX_ENTRIES:
                        application_log[:] = application_log[-MAX_ENTRIES:]
            # Send confirmation SMS
            if caller and TELNYX_PHONE:
                job_name = session.get("selected_job", {}).get("name", "the position")
                try:
                    requests.post(
                        "https://api.telnyx.com/v2/messages",
                        headers=HEADERS,
                        timeout=10,
                        json={
                            "from": TELNYX_PHONE,
                            "to": caller,
                            "text": f"Hi {first_name}, your application for {job_name} has been submitted! Our team will be in touch.",
                        },
                    )
                except Exception as e:
                    app.logger.error("Confirmation SMS failed: %s", e)
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": f"Done, {first_name}. Your application has been submitted and a confirmation text is on the way. Good luck!",
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


@app.route("/jobs", methods=["GET"])
def list_jobs():
    """List open positions from ATS."""
    result = merge_get("/ats/v1/jobs", params={"status": "OPEN", "page_size": 20})
    return jsonify(result or {"results": []})


@app.route("/applications", methods=["GET"])
def list_applications():
    """List applications submitted via hotline."""
    return jsonify({"applications": application_log[-50:]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-recruitment-hotline", "total_applications": len(application_log)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
