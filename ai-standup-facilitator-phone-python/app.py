#!/usr/bin/env python3
"""AI Standup Facilitator Phone — team members call in their daily standup update. AI collects what they did, what they're doing, and blockers, then summarizes for the team."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
STANDUP_NUMBER = os.getenv("STANDUP_NUMBER")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
today_updates = []

SYSTEM_PROMPT = """You are a standup facilitator. Ask three questions one at a time:
1. What did you accomplish yesterday?
2. What are you working on today?
3. Any blockers or things you need help with?
Be brief and encouraging. One sentence per response. After question 3, thank them and say you'll share the summary with the team."""

def call_inference(messages, max_tokens=150):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5}, timeout=15)
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
        active_calls[ccid] = {"caller": data.get("from"), "conversation": [{"role": "system", "content": SYSTEM_PROMPT}], "start": time.time()}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="Good morning! Ready for your standup update? What did you accomplish yesterday?", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended" and call:
        client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=3, timeout_secs=30, language_code="en-US")
        return jsonify({"status": "listening"}), 200
    elif event_type == "call.gather.ended" and call:
        speech = data.get("speech", {}).get("result", "")
        if not speech:
            client.calls.actions.speak(ccid, payload="Take your time.", voice="female", language_code="en-US")
            return jsonify({"status": "waiting"}), 200
        call["conversation"].append({"role": "user", "content": speech})
        response = call_inference(call["conversation"])
        call["conversation"].append({"role": "assistant", "content": response})
        client.calls.actions.speak(ccid, payload=response, voice="female", language_code="en-US")
        return jsonify({"status": "responding"}), 200
    elif event_type == "call.hangup":
        call = active_calls.pop(ccid, None)
        if call and len(call.get("conversation", [])) > 3:
            extract = [{"role": "system", "content": "Extract standup update. Return JSON: yesterday (list of accomplishments), today (list of plans), blockers (list or empty), mood (string)."},
                {"role": "user", "content": chr(10).join(f"{m['role']}: {m['content']}" for m in call["conversation"] if m["role"] != "system")}]
            try:
                update = json.loads(call_inference(extract, max_tokens=300))
                update["caller"] = call["caller"]
                update["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                today_updates.append(update)
                if SLACK_WEBHOOK_URL:
                    yesterday = ", ".join(update.get("yesterday", []))
                    today_plan = ", ".join(update.get("today", []))
                    blockers = ", ".join(update.get("blockers", [])) or "None"
                    requests.post(SLACK_WEBHOOK_URL, json={"text": f"*Standup from {call['caller']}*\n:white_check_mark: Yesterday: {yesterday}\n:arrow_forward: Today: {today_plan}\n:no_entry: Blockers: {blockers}"}, timeout=10)
            except Exception: pass
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/standups", methods=["GET"])
def list_standups():
    return jsonify({"updates": today_updates[-20:]}), 200

@app.route("/standups/summary", methods=["GET"])
def daily_summary():
    if not today_updates: return jsonify({"message": "No updates today"}), 200
    all_blockers = []
    for u in today_updates:
        all_blockers.extend(u.get("blockers", []))
    return jsonify({"team_size": len(today_updates), "has_blockers": len(all_blockers) > 0, "blockers": all_blockers}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "updates_today": len(today_updates)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
