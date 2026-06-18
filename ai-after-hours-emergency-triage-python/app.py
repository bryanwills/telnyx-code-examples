#!/usr/bin/env python3
"""AI After-Hours Emergency Triage — after-hours calls screened by AI. True emergencies get forwarded to on-call; everything else gets a voicemail + next-day callback promise."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
MAIN_NUMBER = os.getenv("MAIN_NUMBER")
ON_CALL_NUMBER = os.getenv("ON_CALL_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
triage_log = []

SYSTEM_PROMPT = """You are an after-hours triage AI. Determine if this is a true emergency requiring immediate attention or something that can wait until business hours.
EMERGENCIES (forward to on-call): system outages affecting production, security breaches, service completely down, safety issues.
NON-EMERGENCIES (take voicemail): billing questions, feature requests, general inquiries, non-critical bugs, account changes.
Ask 1-2 clarifying questions max, then decide. Be empathetic. Keep responses under 2 sentences."""

def call_inference(messages, max_tokens=150):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    call = active_calls.get(ccid)
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_calls[ccid] = {"caller": data.get("from"), "conversation": [{"role": "system", "content": SYSTEM_PROMPT}], "exchanges": 0}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="You've reached after-hours support. I need to understand your situation to route you correctly. What's happening?", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended" and call:
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=2, timeout_secs=20, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended" and call:
        speech = data.get("speech", {}).get("result", "")
        if not speech:
            client.calls.actions.speak(ccid, payload="I didn't catch that. Could you describe what's happening?", voice="female", language_code="en-US")
            return jsonify({"status": "reprompting"}), 200
        call["conversation"].append({"role": "user", "content": speech})
        call["exchanges"] += 1
        if call["exchanges"] >= 2:
            classify = [{"role": "system", "content": "Classify as EMERGENCY or NON_EMERGENCY. Return JSON: classification (string), confidence (float), reason (string, 10 words max)."},
                {"role": "user", "content": chr(10).join(f"{m['role']}: {m['content']}" for m in call["conversation"] if m["role"] != "system")}]
            try:
                result = json.loads(call_inference(classify))
                is_emergency = result.get("classification") == "EMERGENCY"
            except Exception:
                emergency_words = ["down", "outage", "breach", "security", "production", "urgent", "critical"]
                is_emergency = any(w in speech.lower() for w in emergency_words)
            triage_log.append({"caller": call["caller"], "emergency": is_emergency, "exchanges": call["exchanges"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            if is_emergency and ON_CALL_NUMBER:
                client.calls.actions.speak(ccid, payload="This sounds urgent. I'm connecting you to our on-call team right now.", voice="female", language_code="en-US")
            else:
                client.calls.actions.speak(ccid, payload="This can be handled during business hours. Leave a message after the tone and we'll call you back first thing tomorrow.", voice="female", language_code="en-US")
        else:
            response = call_inference(call["conversation"])
            call["conversation"].append({"role": "assistant", "content": response})
            client.calls.actions.speak(ccid, payload=response, voice="female", language_code="en-US")
        return jsonify({"status": "triaging"}), 200
    elif event_type == "call.hangup":
        active_calls.pop(ccid, None)
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/triage-log", methods=["GET"])
def get_log():
    emergencies = sum(1 for t in triage_log if t.get("emergency"))
    return jsonify({"log": triage_log[-50:], "total": len(triage_log), "emergencies": emergencies}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "active": len(active_calls)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
