"""Edge IVR A/B Tester — randomly assign callers to different call flows.
Track completion rates, drop-offs, resolution times. Auto-shift traffic
to the winning variant after statistical significance."""
import os, json, time, random, math, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import boto3

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "ivr-experiments")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MIN_SAMPLE = int(os.getenv("MIN_SAMPLE_SIZE", "100"))

s3 = boto3.client("s3", endpoint_url="https://storage.telnyx.com",
                   aws_access_key_id=TELNYX_API_KEY, aws_secret_access_key=TELNYX_API_KEY)

experiments = {}
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

def get_variant(experiment_id):
    exp = experiments.get(experiment_id)
    if not exp:
        return "A"
    if exp.get("winner"):
        return exp["winner"]
    a_n = exp["variants"]["A"]["calls"]
    b_n = exp["variants"]["B"]["calls"]
    if a_n >= MIN_SAMPLE and b_n >= MIN_SAMPLE:
        a_rate = exp["variants"]["A"]["completions"] / max(a_n, 1)
        b_rate = exp["variants"]["B"]["completions"] / max(b_n, 1)
        pooled = (exp["variants"]["A"]["completions"] + exp["variants"]["B"]["completions"]) / (a_n + b_n)
        if pooled > 0 and pooled < 1:
            se = math.sqrt(pooled * (1 - pooled) * (1/a_n + 1/b_n))
            if se > 0:
                z = abs(a_rate - b_rate) / se
                if z > 1.96:
                    winner = "A" if a_rate > b_rate else "B"
                    exp["winner"] = winner
                    app.logger.info("Experiment %s winner: %s (A=%.2f B=%.2f z=%.2f)", experiment_id, winner, a_rate, b_rate, z)
                    return winner
    return random.choice(["A", "B"])

@app.route("/experiments", methods=["POST"])
def create_experiment():
    data = request.get_json() or {}
    exp_id = data.get("id", f"exp-{int(time.time())}")
    experiments[exp_id] = {
        "id": exp_id, "created": time.time(),
        "variant_a_greeting": data.get("variant_a_greeting", "Press 1 for support, 2 for sales."),
        "variant_b_greeting": data.get("variant_b_greeting", "Tell me how I can help you today."),
        "variant_a_gather": data.get("variant_a_gather", "dtmf"),
        "variant_b_gather": data.get("variant_b_gather", "speech"),
        "winner": None,
        "variants": {"A": {"calls": 0, "completions": 0, "dropoffs": 0, "total_duration": 0},
                      "B": {"calls": 0, "completions": 0, "dropoffs": 0, "total_duration": 0}}
    }
    return jsonify({"status": "created", "experiment": experiments[exp_id]})

@app.route("/experiments", methods=["GET"])
def list_experiments():
    return jsonify({"experiments": list(experiments.values())})

@app.route("/experiments/<exp_id>", methods=["GET"])
def get_experiment(exp_id):
    exp = experiments.get(exp_id)
    if not exp:
        return jsonify({"error": "Not found"}), 404
    return jsonify(exp)

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    cc_id = event.get("payload", {}).get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.initiated":
        if event.get("payload", {}).get("direction") == "incoming":
            exp_id = list(experiments.keys())[-1] if experiments else None
            variant = get_variant(exp_id) if exp_id else "A"
            call_sessions[cc_id] = {"exp_id": exp_id, "variant": variant, "start": time.time(), "ts": time.time()}
            ttl_cleanup(call_sessions)
            if exp_id:
                experiments[exp_id]["variants"][variant]["calls"] += 1
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
                          headers=HEADERS, timeout=10,
                          json={"client_state": encode_state({"exp": exp_id, "var": variant, "step": "greeting"})})

    elif event_type == "call.answered":
        state = decode_state(event.get("payload", {}).get("client_state", ""))
        exp_id = state.get("exp")
        variant = state.get("var", "A")
        exp = experiments.get(exp_id, {})
        greeting = exp.get(f"variant_{variant.lower()}_greeting", "Welcome.")
        gather_type = exp.get(f"variant_{variant.lower()}_gather", "dtmf")
        if gather_type == "speech":
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": greeting, "voice": "female", "language": "en-US",
                                "input_type": "speech", "minimum_digits": 1,
                                "client_state": encode_state({"exp": exp_id, "var": variant, "step": "gather"})})
        else:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": greeting, "voice": "female", "language": "en-US",
                                "minimum_digits": 1, "maximum_digits": 1,
                                "client_state": encode_state({"exp": exp_id, "var": variant, "step": "gather"})})

    elif event_type == "call.gather.ended":
        state = decode_state(event.get("payload", {}).get("client_state", ""))
        exp_id = state.get("exp")
        variant = state.get("var", "A")
        if exp_id and exp_id in experiments:
            experiments[exp_id]["variants"][variant]["completions"] += 1
            session = call_sessions.get(cc_id, {})
            duration = time.time() - session.get("start", time.time())
            experiments[exp_id]["variants"][variant]["total_duration"] += duration
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": "Thank you. Connecting you now.", "voice": "female", "language": "en-US"})

    elif event_type == "call.hangup":
        session = call_sessions.pop(cc_id, {})
        exp_id = session.get("exp_id")
        variant = session.get("variant", "A")
        if exp_id and exp_id in experiments and not session.get("completed"):
            experiments[exp_id]["variants"][variant]["dropoffs"] += 1

    return jsonify({"status": "ok"})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-ivr-ab-tester"})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
