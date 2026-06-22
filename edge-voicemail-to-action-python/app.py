"""Edge Voicemail to Action — voicemail arrives, AI transcribes, classifies, and acts.
Urgent: immediately calls on-call person with spoken briefing.
Routine: hourly SMS digest. Spam: deleted, number blocklisted."""
import os, json, time, threading, base64, logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import requests

load_dotenv()
app = Flask(__name__)
app.logger.setLevel(logging.INFO)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_PUBLIC_KEY = os.getenv("TELNYX_PUBLIC_KEY", "")
MAX_TIMESTAMP_SKEW = 300  # seconds; reject replayed/stale webhooks
TELNYX_PHONE = os.getenv("TELNYX_PHONE_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
ONCALL_NUMBER = os.getenv("ONCALL_NUMBER")
DIGEST_RECIPIENTS = os.getenv("DIGEST_RECIPIENTS", "").split(",")
HOST = os.getenv("HOST", "127.0.0.1")
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

voicemails = []
routine_queue = []
spam_blocklist = set()
MAX_ENTRIES = 10000

def verify_telnyx_signature(raw_body: bytes) -> bool:
    """Verify the Telnyx Ed25519 webhook signature over "<timestamp>|<raw body>".

    Native verification (no SDK dependency) suited to edge deployments: decodes the
    Portal public key, checks the signature, and rejects stale/replayed timestamps.
    """
    if not TELNYX_PUBLIC_KEY:
        app.logger.error("TELNYX_PUBLIC_KEY not configured; rejecting webhook")
        return False
    signature = request.headers.get("telnyx-signature-ed25519", "")
    timestamp = request.headers.get("telnyx-timestamp", "")
    if not signature or not timestamp:
        return False
    try:
        if abs(time.time() - int(timestamp)) > MAX_TIMESTAMP_SKEW:
            return False
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(TELNYX_PUBLIC_KEY))
        signed_payload = f"{timestamp}|".encode() + raw_body
        public_key.verify(base64.b64decode(signature), signed_payload)
        return True
    except (InvalidSignature, ValueError, TypeError) as e:
        app.logger.error("Webhook signature verification failed: %s", e)
        return False


CLASSIFY_PROMPT = """Classify this voicemail transcription. Respond with JSON only:
{"classification": "urgent|routine|spam", "summary": "one line summary", "callback_number": "extracted phone or null", "entities": ["key entities mentioned"]}

Urgent: medical, security, system down, legal deadline, customer emergency.
Routine: appointment confirmations, general inquiries, follow-ups.
Spam: robocalls, solicitations, scams, silence."""

def classify_voicemail(transcript):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": CLASSIFY_PROMPT},
                         {"role": "user", "content": transcript}],
            "response_format": {"type": "json_object"}
        })
        if resp.ok:
            return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        app.logger.error("Classification failed: %s", e)
    return {"classification": "routine", "summary": transcript[:100]}

def call_oncall(voicemail_data):
    if not ONCALL_NUMBER:
        return
    try:
        summary = voicemail_data.get("summary", "urgent voicemail")
        caller = voicemail_data.get("from", "unknown")
        requests.post("https://api.telnyx.com/v2/calls", headers=HEADERS, timeout=10, json={
            "connection_id": os.getenv("TELNYX_CONNECTION_ID", ""),
            "to": ONCALL_NUMBER, "from": TELNYX_PHONE,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/oncall"
        })
        app.logger.info("Calling on-call for urgent voicemail from %s", caller)
    except Exception as e:
        app.logger.error("On-call escalation failed: %s", e)

def send_digest():
    while True:
        time.sleep(3600)
        if not routine_queue:
            continue
        batch = routine_queue.copy()
        routine_queue.clear()
        digest_text = f"{len(batch)} voicemail(s):\n"
        for vm in batch[:20]:
            digest_text += f"- {vm.get('from', '?')}: {vm.get('summary', '')}\n"
        for recipient in DIGEST_RECIPIENTS:
            recipient = recipient.strip()
            if not recipient:
                continue
            try:
                requests.post("https://api.telnyx.com/v2/messages", headers=HEADERS, timeout=10,
                              json={"from": TELNYX_PHONE, "to": recipient, "text": digest_text})
            except Exception as e:
                app.logger.error("Digest SMS to %s failed: %s", recipient, e)

digest_thread = threading.Thread(target=send_digest, daemon=True)
digest_thread.start()

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    raw_body = request.get_data()  # capture the RAW body for signature verification
    if not verify_telnyx_signature(raw_body):
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
    caller = ep.get("from", "")

    if event_type == "call.initiated" and ep.get("direction") == "incoming":
        if caller in spam_blocklist:
            requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/reject",
                          headers=HEADERS, timeout=10)
            return jsonify({"status": "blocked"})
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/answer",
                      headers=HEADERS, timeout=10,
                      json={"client_state": base64.b64encode(json.dumps({"from": caller}).encode()).decode()})

    elif event_type == "call.answered":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/gather_using_speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": "Please leave your message after the tone. Press pound when finished.",
                            "voice": "female", "language": "en-US",
                            "input_type": "speech", "timeout_secs": 120,
                            "client_state": ep.get("client_state", "")})

    elif event_type == "call.gather.ended":
        transcript = ep.get("speech", {}).get("result", "")
        caller = json.loads(base64.b64decode(ep.get("client_state", "")).decode()).get("from", "") if ep.get("client_state") else ""
        if transcript:
            result = classify_voicemail(transcript)
            vm_record = {"from": caller, "transcript": transcript, "ts": time.time(), **result}
            voicemails.append(vm_record)
            if len(voicemails) > MAX_ENTRIES:
                voicemails[:] = voicemails[-MAX_ENTRIES:]
            classification = result.get("classification", "routine")
            if classification == "urgent":
                call_oncall(vm_record)
            elif classification == "spam":
                spam_blocklist.add(caller)
                app.logger.info("Spam voicemail from %s — blocklisted", caller)
            else:
                routine_queue.append(vm_record)
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": "Thank you. Your message has been received.", "voice": "female", "language": "en-US"})

    elif event_type == "call.speak.ended":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
                      headers=HEADERS, timeout=10)

    elif event_type == "call.hangup":
        pass

    return jsonify({"status": "ok"})

@app.route("/webhooks/oncall", methods=["POST"])
def handle_oncall():
    raw_body = request.get_data()  # capture the RAW body for signature verification
    if not verify_telnyx_signature(raw_body):
        return jsonify({"error": "invalid signature"}), 401
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    cc_id = event.get("payload", {}).get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.answered":
        urgent = [v for v in voicemails if v.get("classification") == "urgent"]
        latest = urgent[-1] if urgent else {}
        briefing = f"Urgent voicemail from {latest.get('from', 'unknown')}. {latest.get('summary', 'No details available.')}."
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/speak",
                      headers=HEADERS, timeout=10,
                      json={"payload": briefing, "voice": "female", "language": "en-US"})

    elif event_type == "call.speak.ended":
        requests.post(f"https://api.telnyx.com/v2/calls/{cc_id}/actions/hangup",
                      headers=HEADERS, timeout=10)

    return jsonify({"status": "ok"})

@app.route("/voicemails", methods=["GET"])
def get_voicemails():
    classification = request.args.get("classification")
    limit = request.args.get("limit", 50, type=int)
    filtered = [v for v in voicemails if not classification or v.get("classification") == classification]
    return jsonify({"voicemails": filtered[-limit:], "total": len(filtered)})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "edge-voicemail-to-action",
                    "voicemails": len(voicemails), "routine_queue": len(routine_queue),
                    "blocklist": len(spam_blocklist)})

if __name__ == "__main__":
    app.run(host=HOST, port=int(os.getenv("PORT", "5000")), debug=False)
