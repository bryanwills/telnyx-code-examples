"""Merge Interview Pipeline — ATS webhook fires on new applicant. Calls candidate
within 60 seconds. AI conducts structured phone screen with role-specific questions.
Scores responses. Updates ATS with results. SMS confirmation to candidate."""
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
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {
    "Authorization": f"Bearer {MERGE_API_KEY}",
    "X-Account-Token": MERGE_ACCOUNT_TOKEN or "",
    "Content-Type": "application/json",
}
MERGE_BASE = "https://api.merge.dev/api"

SCREEN_QUESTIONS = [
    "Tell me about your most relevant experience for this role.",
    "What attracted you to this position?",
    "Describe a challenging project you led and the outcome.",
    "What is your availability to start, and are you open to the listed location?",
    "Do you have any questions about the role or company?",
]

call_sessions = {}
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
                            "You are a professional recruiter conducting a phone screen. "
                            "Score answers 1-5. Be warm but efficient. One question at a time. "
                            "Keep responses under 2 sentences.\n\n"
                            f"Context: {json.dumps(context)}"
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
    return "I could not process that. Let me move to the next question."


def score_screen(answers):
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
                            "Score this phone screen. Return JSON: "
                            '{"overall_score": 1-5, "strengths": ["..."], '
                            '"concerns": ["..."], "recommendation": '
                            '"advance|hold|reject", "summary": "2 sentences"}'
                        ),
                    },
                    {"role": "user", "content": json.dumps(answers)},
                ],
                "response_format": {"type": "json_object"},
            },
        )
        if resp.ok:
            return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        app.logger.error("Scoring failed: %s", e)
    return {"overall_score": 3, "recommendation": "hold", "summary": "Auto-score unavailable."}


@app.route("/webhooks/ats", methods=["POST"])
def handle_ats_webhook():
    """Merge ATS webhook — new application triggers outbound screen call."""
    data = request.get_json() or {}
    candidate_id = data.get("candidate", data.get("candidate_id", ""))
    application_id = data.get("id", data.get("application_id", ""))
    job_name = data.get("job_name", "the open position")
    if not candidate_id:
        return jsonify({"error": "No candidate ID"}), 400
    candidate = merge_get(f"/ats/v1/candidates/{candidate_id}")
    if not candidate:
        return jsonify({"error": "Candidate not found in ATS"}), 404
    phone = None
    for pn in candidate.get("phone_numbers", []):
        if pn.get("value"):
            phone = pn["value"]
            break
    if not phone:
        app.logger.warning("Candidate %s has no phone number", candidate_id)
        return jsonify({"error": "No phone number on file"}), 400
    session_id = f"screen-{int(time.time())}-{candidate_id[:8]}"
    call_sessions[session_id] = {
        "candidate_id": candidate_id,
        "application_id": application_id,
        "candidate_name": f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip(),
        "job_name": job_name,
        "phone": phone,
        "question_idx": 0,
        "answers": [],
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
    except Exception as e:
        app.logger.error("Outbound call failed: %s", e)
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "calling", "session_id": session_id, "candidate": call_sessions[session_id]["candidate_name"]})


@app.route("/screen", methods=["POST"])
def manual_screen():
    """Manually trigger a phone screen."""
    data = request.get_json() or {}
    phone = data.get("phone")
    name = data.get("name", "Candidate")
    job = data.get("job_name", "Open Position")
    if not phone:
        return jsonify({"error": "phone required"}), 400
    session_id = f"screen-{int(time.time())}"
    call_sessions[session_id] = {
        "candidate_name": name,
        "job_name": job,
        "phone": phone,
        "question_idx": 0,
        "answers": [],
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "calling", "session_id": session_id})


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
        name = session.get("candidate_name", "")
        job = session.get("job_name", "the position")
        greeting = (
            f"Hi {name}, this is an automated phone screen for {job}. "
            f"I will ask you {len(SCREEN_QUESTIONS)} questions. Ready? "
            f"Here is the first one. {SCREEN_QUESTIONS[0]}"
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
                "timeout_secs": 60,
                "client_state": encode_state({"session_id": session_id, "q_idx": 0}),
            },
        )

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        q_idx = state.get("q_idx", 0)
        if speech and session:
            session.setdefault("answers", []).append(
                {"question": SCREEN_QUESTIONS[q_idx], "answer": speech}
            )
            next_idx = q_idx + 1
            if next_idx < len(SCREEN_QUESTIONS):
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": f"Thank you. Next question. {SCREEN_QUESTIONS[next_idx]}",
                        "voice": "female",
                        "language": "en-US",
                        "input_type": "speech",
                        "timeout_secs": 60,
                        "client_state": encode_state({"session_id": session_id, "q_idx": next_idx}),
                    },
                )
            else:
                scorecard = score_screen(session["answers"])
                session["scorecard"] = scorecard
                app_id = session.get("application_id")
                if app_id:
                    merge_patch(
                        f"/ats/v1/applications/{app_id}",
                        {"current_stage": "phone_screen_complete"},
                    )
                phone = session.get("phone")
                if phone and TELNYX_PHONE:
                    try:
                        requests.post(
                            "https://api.telnyx.com/v2/messages",
                            headers=HEADERS,
                            timeout=10,
                            json={
                                "from": TELNYX_PHONE,
                                "to": phone,
                                "text": (
                                    f"Thanks for completing the phone screen for "
                                    f"{session.get('job_name', 'the position')}! "
                                    f"Our team will be in touch within 2 business days."
                                ),
                            },
                        )
                    except Exception as e:
                        app.logger.error("Confirmation SMS failed: %s", e)
                requests.post(
                    f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                    headers=HEADERS,
                    timeout=10,
                    json={
                        "payload": "That is all the questions. Thank you for your time. You will hear from us within two business days. Goodbye.",
                        "voice": "female",
                        "language": "en-US",
                    },
                )
        else:
            requests.post(
                f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                headers=HEADERS,
                timeout=10,
                json={
                    "payload": "I did not catch that. Could you repeat your answer?",
                    "voice": "female",
                    "language": "en-US",
                    "input_type": "speech",
                    "timeout_secs": 60,
                    "client_state": encode_state({"session_id": session_id, "q_idx": state.get("q_idx", 0)}),
                },
            )

    elif event_type == "call.speak.ended":
        requests.post(
            f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
            headers=HEADERS,
            timeout=10,
        )

    elif event_type == "call.hangup":
        pass  # keep session for scorecard retrieval

    return jsonify({"status": "ok"})


@app.route("/screens", methods=["GET"])
def list_screens():
    """List all completed screens with scores."""
    results = []
    for sid, s in call_sessions.items():
        results.append({
            "session_id": sid,
            "candidate": s.get("candidate_name"),
            "job": s.get("job_name"),
            "answers": len(s.get("answers", [])),
            "scorecard": s.get("scorecard"),
        })
    return jsonify({"screens": results})


@app.route("/screens/<session_id>", methods=["GET"])
def get_screen(session_id):
    """Get a specific screen result."""
    session = call_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    return jsonify(session)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "merge-interview-pipeline", "active_screens": len(call_sessions)})


if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
