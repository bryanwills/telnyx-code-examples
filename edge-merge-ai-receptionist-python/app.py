"""Edge Merge AI Receptionist — edge worker answers calls, matches caller against
Merge HRIS employees AND CRM contacts. Internal: transfer. External known contact:
pull deal context, whisper brief. Unknown: screen and take message."""
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
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
MERGE_API_KEY = os.getenv("MERGE_API_KEY")
MERGE_ACCOUNT_TOKEN = os.getenv("MERGE_ACCOUNT_TOKEN")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}
MERGE_HEADERS = {"Authorization": f"Bearer {MERGE_API_KEY}", "X-Account-Token": MERGE_ACCOUNT_TOKEN or "", "Content-Type": "application/json"}
MERGE_BASE = "https://api.merge.dev/api"

call_sessions = {}
messages = []
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

def find_employee_by_name(name):
    result = merge_get("/hris/v1/employees", params={"display_full_name": name})
    if result and result.get("results"):
        return result["results"][0]
    return None

def find_crm_contact(name):
    result = merge_get("/crm/v1/contacts", params={"name": name})
    if result and result.get("results"):
        return result["results"][0]
    return None

def get_deals_for_contact(contact_id):
    result = merge_get("/crm/v1/opportunities", params={"contact_id": contact_id})
    return (result or {}).get("results", [])

def call_inference(prompt, context):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": f"You are a professional receptionist. Use this context to route the call:\n{json.dumps(context)}\nBe concise. 1-2 sentences."},
                {"role": "user", "content": prompt}
            ]
        })
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        app.logger.error("Inference failed: %s", e)
    return "Let me transfer you now."

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
        caller = ep.get("from", "")
        call_sessions[cc_id] = {"caller": caller, "ts": time.time()}
        ttl_cleanup(call_sessions)
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
                      headers=HEADERS, timeout=10,
                      json={"client_state": encode_state({"step": "greeting"})})

    elif event_type == "call.answered":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": "Thank you for calling. Who would you like to speak with?",
                            "voice": "female", "language": "en-US", "input_type": "speech", "timeout_secs": 15,
                            "client_state": encode_state({"step": "who"})})

    elif event_type == "call.gather.ended":
        speech = ep.get("speech", {}).get("result", "")
        state = decode_state(ep.get("client_state", ""))
        session = call_sessions.get(cc_id, {})

        if state.get("step") == "who" and speech:
            employee = find_employee_by_name(speech)
            if employee:
                emp_phone = None
                for pn in employee.get("phone_numbers", []):
                    if pn.get("value"):
                        emp_phone = pn["value"]
                        break
                if emp_phone:
                    requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                                  headers=HEADERS, timeout=10,
                                  json={"payload": f"Connecting you to {employee.get('first_name', '')} now.",
                                        "voice": "female", "language": "en-US",
                                        "client_state": encode_state({"step": "transferring", "target": emp_phone})})
                    return jsonify({"status": "ok"})
            contact = find_crm_contact(speech)
            if contact:
                deals = get_deals_for_contact(contact.get("id", ""))
                session["context"] = {"contact": contact.get("name"), "deals": len(deals)}
                requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                              headers=HEADERS, timeout=10,
                              json={"payload": f"I found {speech} in our system. How can I help you today?",
                                    "voice": "female", "language": "en-US", "input_type": "speech", "timeout_secs": 30,
                                    "client_state": encode_state({"step": "conversation"})})
            else:
                requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                              headers=HEADERS, timeout=10,
                              json={"payload": "I could not find that person. Can I take a message?",
                                    "voice": "female", "language": "en-US", "input_type": "speech", "timeout_secs": 60,
                                    "client_state": encode_state({"step": "message"})})

        elif state.get("step") == "message" and speech:
            messages.append({"caller": session.get("caller"), "message": speech, "ts": time.time()})
            if len(messages) > MAX_ENTRIES:
                messages[:] = messages[-MAX_ENTRIES:]
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": "Thank you. I have recorded your message. Goodbye.",
                                "voice": "female", "language": "en-US"})

        elif state.get("step") == "conversation" and speech:
            context = session.get("context", {})
            response = call_inference(speech, context)
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                          headers=HEADERS, timeout=10,
                          json={"payload": response, "voice": "female", "language": "en-US",
                                "input_type": "speech", "timeout_secs": 30,
                                "client_state": encode_state({"step": "conversation"})})

    elif event_type == "call.speak.ended":
        state = decode_state(ep.get("client_state", ""))
        if state.get("step") == "transferring":
            target = state.get("target")
            if target:
                requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/transfer",
                              headers=HEADERS, timeout=10, json={"to": target})
        else:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
                          headers=HEADERS, timeout=10)

    elif event_type == "call.hangup":
        call_sessions.pop(cc_id, None)

    return jsonify({"status": "ok"})

@app.route("/messages", methods=["GET"])
def get_messages():
    return jsonify({"messages": messages[-50:]})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-merge-ai-receptionist"})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
