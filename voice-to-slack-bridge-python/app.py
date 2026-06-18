#!/usr/bin/env python3
"""Voice-to-Slack Bridge — call a phone number, speak a message, AI transcribes and posts to Slack with urgency tagging."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
BRIDGE_NUMBER = os.getenv("BRIDGE_NUMBER")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
messages_posted = []

def post_to_slack(text, urgency="normal"):
    emoji = {"critical": ":rotating_light:", "high": ":warning:", "normal": ":speech_balloon:", "low": ":information_source:"}
    if SLACK_WEBHOOK_URL:
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": f"{emoji.get(urgency, '')} {text}"}, timeout=10)
        except Exception as e:
            app.logger.error(f"Slack post failed: {e}")

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_calls[ccid] = {"caller": data.get("from"), "messages": []}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="Slack bridge. Speak your message after the tone. Press pound when done.", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended":
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=3, timeout_secs=60, language_code="en-US", terminating_digit="#")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended":
        call = active_calls.get(ccid)
        speech = data.get("speech", {}).get("result", "")
        if call and speech:
            try:
                resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                    json={"model": AI_MODEL, "messages": [{"role": "system", "content": "Classify urgency of this voice message as critical/high/normal/low. Return JSON: urgency (string), cleaned_message (string, cleaned up speech-to-text artifacts), summary (1 sentence)."},
                        {"role": "user", "content": speech}], "max_tokens": 150, "temperature": 0.2}, timeout=15)
                analysis = json.loads(resp.json()["choices"][0]["message"]["content"])
                urgency = analysis.get("urgency", "normal")
                clean_msg = analysis.get("cleaned_message", speech)
            except Exception:
                urgency, clean_msg = "normal", speech
            caller = call.get("caller", "unknown")
            slack_msg = f"*Voice message from {caller}*\n{clean_msg}"
            post_to_slack(slack_msg, urgency)
            messages_posted.append({"caller": caller, "message": clean_msg, "urgency": urgency, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            client.calls.actions.speak(ccid, payload="Message posted to Slack. Goodbye!", voice="female", language_code="en-US")
        return jsonify({"status": "posted"}), 200
    elif event_type == "call.hangup":
        active_calls.pop(ccid, None)
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/messages", methods=["GET"])
def list_messages():
    return jsonify({"messages": messages_posted[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "posted": len(messages_posted)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
