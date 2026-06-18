#!/usr/bin/env python3
"""AI Event RSVP Phone Line — call to RSVP for an event. AI collects guest info, dietary restrictions, plus-ones, and confirms the reservation."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
RSVP_NUMBER = os.getenv("RSVP_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
rsvps = []

EVENT = {"name": "Annual Company Gala", "date": "Saturday, July 12th", "time": "7:00 PM", "venue": "The Grand Ballroom, 123 Main St", "dress_code": "Black tie"}

SYSTEM_PROMPT = f"""You are the RSVP line for {EVENT['name']} on {EVENT['date']} at {EVENT['time']}, {EVENT['venue']}. Dress code: {EVENT['dress_code']}.
Collect: 1) Full name 2) Number of guests (including them) 3) Dietary restrictions (vegetarian, vegan, gluten-free, allergies) 4) Any accessibility needs.
Be warm and excited. Confirm all details before ending. Keep responses under 2 sentences."""

def call_inference(messages, max_tokens=150):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.6}, timeout=15)
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
        active_calls[ccid] = {"caller": data.get("from"), "conversation": [{"role": "system", "content": SYSTEM_PROMPT}]}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload=f"Welcome! You've reached the RSVP line for the {EVENT['name']}. We'd love to have you! Can I get your full name?", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended" and call:
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=2, timeout_secs=15, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended" and call:
        speech = data.get("speech", {}).get("result", "")
        if not speech:
            client.calls.actions.speak(ccid, payload="Sorry, I missed that. Could you repeat?", voice="female", language_code="en-US")
            return jsonify({"status": "reprompting"}), 200
        call["conversation"].append({"role": "user", "content": speech})
        response = call_inference(call["conversation"])
        call["conversation"].append({"role": "assistant", "content": response})
        client.calls.actions.speak(ccid, payload=response, voice="female", language_code="en-US")
        return jsonify({"status": "responding"}), 200
    elif event_type == "call.hangup":
        call = active_calls.pop(ccid, None)
        if call and len(call.get("conversation", [])) > 3:
            extract = [{"role": "system", "content": "Extract RSVP. Return JSON: name (string), guests (number), dietary (list), accessibility (string or null), confirmed (boolean)."},
                {"role": "user", "content": chr(10).join(f"{m['role']}: {m['content']}" for m in call["conversation"] if m["role"] != "system")}]
            try:
                rsvp = json.loads(call_inference(extract, max_tokens=200))
                rsvp["caller"] = call["caller"]
                rsvp["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                rsvps.append(rsvp)
            except Exception: pass
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/rsvps", methods=["GET"])
def list_rsvps():
    total_guests = sum(r.get("guests", 1) for r in rsvps)
    return jsonify({"rsvps": rsvps, "total_parties": len(rsvps), "total_guests": total_guests}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "rsvps": len(rsvps)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
