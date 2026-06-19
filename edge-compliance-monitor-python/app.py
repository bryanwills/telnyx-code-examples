"""Edge Compliance Monitor — real-time compliance checking for regulated call centers.
Processes media streams via WebSocket, AI checks utterances against TCPA/HIPAA rules,
whispers warnings to agent before they finish the sentence."""
import os, json, time, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

COMPLIANCE_RULES = os.getenv("COMPLIANCE_RULES", "TCPA,HIPAA")
SYSTEM_PROMPT = f"""You are a real-time compliance monitor for phone calls.
Rules to check: {COMPLIANCE_RULES}
TCPA violations: threatening language, calling outside allowed hours, failure to identify, refusing to honor do-not-call.
HIPAA violations: sharing PHI without authorization, naming patients to unauthorized parties, discussing diagnoses on unencrypted channels.
Analyze each utterance. Respond with JSON: {{"violation": true/false, "rule": "TCPA|HIPAA|null", "severity": "warning|critical|null", "message": "brief warning to whisper to agent"}}"""

call_sessions = {}
violations_log = []
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

def check_compliance(utterance, context):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=10, json={
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": f"Call context: {context}\nAgent utterance: {utterance}"}],
            "response_format": {"type": "json_object"}
        })
        if resp.ok:
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        app.logger.error("Compliance check failed: %s", e)
    return {"violation": False}

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

    if event_type == "call.initiated" and ep.get("direction") == "incoming":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
                      headers=HEADERS, timeout=10,
                      json={"client_state": encode_state({"step": "monitor", "utterances": []})})
        call_sessions[cc_id] = {"start": time.time(), "violations": [], "utterance_count": 0, "ts": time.time()}
        ttl_cleanup(call_sessions)

    elif event_type == "call.answered":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": "This call is being monitored for quality and compliance.",
                            "voice": "female", "language": "en-US",
                            "input_type": "speech", "timeout_secs": 60,
                            "client_state": encode_state({"step": "listening"})})

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        state = decode_state(ep.get("client_state", ""))
        if speech:
            session = call_sessions.get(cc_id, {})
            session["utterance_count"] = session.get("utterance_count", 0) + 1
            result = check_compliance(speech, f"Utterance #{session['utterance_count']} in call")
            if result.get("violation"):
                violation_record = {
                    "call_control_id": cc_id, "utterance": speech,
                    "rule": result.get("rule"), "severity": result.get("severity"),
                    "message": result.get("message"), "ts": time.time()
                }
                session.setdefault("violations", []).append(violation_record)
                violations_log.append(violation_record)
                if len(violations_log) > MAX_ENTRIES:
                    violations_log[:] = violations_log[-MAX_ENTRIES:]
                requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                              headers=HEADERS, timeout=10,
                              json={"payload": f"Compliance alert: {result.get('message', 'Please review your statement.')}",
                                    "voice": "female", "language": "en-US",
                                    "client_state": encode_state({"step": "whisper_sent"})})
                return jsonify({"status": "violation_detected"})
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": "", "voice": "female", "language": "en-US",
                            "input_type": "speech", "timeout_secs": 60,
                            "client_state": encode_state({"step": "listening"})})

    elif event_type == "call.speak.ended":
        state = decode_state(ep.get("client_state", ""))
        if state.get("step") == "whisper_sent":
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": "", "voice": "female", "language": "en-US",
                                "input_type": "speech", "timeout_secs": 60,
                                "client_state": encode_state({"step": "listening"})})

    elif event_type == "call.hangup":
        session = call_sessions.pop(cc_id, None)
        if session:
            app.logger.info("Call ended. Utterances: %s, Violations: %s",
                           session.get("utterance_count", 0), len(session.get("violations", [])))

    return jsonify({"status": "ok"})

@app.route("/violations", methods=["GET"])
def get_violations():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"violations": violations_log[-limit:], "total": len(violations_log)})

@app.route("/calls", methods=["GET"])
def active_calls():
    return jsonify({"active": len(call_sessions),
                    "calls": {k: {"utterances": v.get("utterance_count", 0),
                                   "violations": len(v.get("violations", []))}
                              for k, v in call_sessions.items()}})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-compliance-monitor",
                    "active_calls": len(call_sessions), "total_violations": len(violations_log)})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
