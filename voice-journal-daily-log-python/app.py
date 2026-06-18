#!/usr/bin/env python3
"""Voice Journal Daily Log — call a number, speak your daily journal entry, AI transcribes and organizes it with mood, topics, and gratitude extraction."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
JOURNAL_NUMBER = os.getenv("JOURNAL_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
journal_entries = []

def call_inference(messages, max_tokens=400):
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
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_calls[ccid] = {"caller": data.get("from"), "entries": [], "start": time.time()}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        ts = time.strftime("%A, %B %d")
        client.calls.actions.speak(ccid, payload=f"Good day. It's {ts}. Tell me about your day. I'm listening.", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended":
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=4, timeout_secs=120, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended":
        call = active_calls.get(ccid)
        speech = data.get("speech", {}).get("result", "")
        if call and speech:
            call["entries"].append(speech)
            if len(call["entries"]) < 3:
                client.calls.actions.speak(ccid, payload="Got it. Anything else you want to capture?", voice="female", language_code="en-US")
            else:
                client.calls.actions.speak(ccid, payload="Beautiful entry. I'll organize this for you. Have a great day.", voice="female", language_code="en-US")
        elif call:
            client.calls.actions.speak(ccid, payload="Entry saved. Take care.", voice="female", language_code="en-US")
        return jsonify({"status": "captured"}), 200
    elif event_type == "call.hangup":
        call = active_calls.pop(ccid, None)
        if call and call["entries"]:
            raw = " ".join(call["entries"])
            try:
                analysis = call_inference([{"role": "system", "content": "Analyze this journal entry. Return JSON: date (today), summary (2-3 sentences), mood (word), energy_level (1-10), topics (list), gratitude_items (list), action_items (list), word_count (int)."},
                    {"role": "user", "content": raw}], max_tokens=400)
                entry = json.loads(analysis)
            except Exception:
                entry = {"raw": raw}
            entry["caller"] = call["caller"]
            entry["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            entry["duration"] = int(time.time() - call["start"])
            journal_entries.append(entry)
        return jsonify({"status": "saved"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/journal", methods=["GET"])
def list_entries():
    return jsonify({"entries": journal_entries[-30:]}), 200

@app.route("/journal/insights", methods=["GET"])
def insights():
    if not journal_entries:
        return jsonify({"message": "No entries yet"}), 200
    moods = [e.get("mood", "unknown") for e in journal_entries[-7:]]
    topics = []
    for e in journal_entries[-7:]:
        topics.extend(e.get("topics", []))
    return jsonify({"recent_moods": moods, "top_topics": list(set(topics))[:10], "streak": len(journal_entries)}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "entries": len(journal_entries)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
