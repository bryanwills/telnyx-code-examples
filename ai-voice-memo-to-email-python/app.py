#!/usr/bin/env python3
"""AI Voice Memo to Email — call a number, dictate a memo, AI cleans it up and sends it as a formatted email via Telnyx."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
MEMO_NUMBER = os.getenv("MEMO_NUMBER")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "memos@example.com")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
memos = []

def call_inference(messages, max_tokens=400):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def send_email(to, subject, body):
    try:
        requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"from": {"email_address": f"memo@{MEMO_NUMBER.replace('+','')}.telnyx.com"} if MEMO_NUMBER else {"email_address": "memo@telnyx.com"},
                "to": [{"email_address": to}], "subject": subject, "body": body, "type": "email"}, timeout=15)
    except Exception as e:
        app.logger.error(f"Email send failed (expected - may need Telnyx email setup): {e}")

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_calls[ccid] = {"caller": data.get("from"), "raw_text": [], "start": time.time()}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="Voice memo. Speak your memo after the tone. Press pound when finished.", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended":
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=5, timeout_secs=120, language_code="en-US", terminating_digit="#")
        return jsonify({"status": "recording"}), 200
    elif event_type == "call.gather.ended":
        call = active_calls.get(ccid)
        speech = data.get("speech", {}).get("result", "")
        if call and speech:
            call["raw_text"].append(speech)
            try:
                formatted = call_inference([{"role": "system", "content": "Clean up this voice memo into a well-formatted email. Fix grammar, add structure (paragraphs, bullets if needed). Return JSON: subject (string, inferred from content), body (string, the formatted memo), action_items (list of strings)."},
                    {"role": "user", "content": speech}])
                memo = json.loads(formatted)
                memo["caller"] = call["caller"]
                memo["raw"] = speech
                memo["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                memos.append(memo)
                send_email(DEFAULT_EMAIL, memo.get("subject", "Voice Memo"), memo.get("body", speech))
                client.calls.actions.speak(ccid, payload=f"Memo saved and emailed. Subject: {memo.get('subject', 'Voice Memo')}. Goodbye!", voice="female", language_code="en-US")
            except Exception:
                memos.append({"raw": speech, "caller": call["caller"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
                client.calls.actions.speak(ccid, payload="Memo saved. Goodbye!", voice="female", language_code="en-US")
        return jsonify({"status": "processed"}), 200
    elif event_type == "call.hangup":
        active_calls.pop(ccid, None)
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/memos", methods=["GET"])
def list_memos():
    return jsonify({"memos": memos[-20:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "memos": len(memos)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
