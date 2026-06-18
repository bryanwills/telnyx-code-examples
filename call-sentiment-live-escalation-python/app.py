#!/usr/bin/env python3
"""Call Sentiment Live Escalation — monitor call transcripts in real-time. When negative sentiment or distress is detected, auto-escalate to a supervisor."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
SUPERVISOR_NUMBER = os.getenv("SUPERVISOR_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
monitored_calls = {}
escalations = []

TRIGGER_WORDS = ["cancel", "lawsuit", "attorney", "supervisor", "manager", "unacceptable", "furious", "ridiculous", "terrible"]

def analyze_sentiment(text):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": [{"role": "system", "content": "Analyze customer sentiment. Return JSON: sentiment (positive/neutral/negative/hostile), score (-1.0 to 1.0), escalate (boolean - true if customer is very upset, threatening, or requesting supervisor), reason (string, 5 words max)."},
            {"role": "user", "content": text}], "max_tokens": 80, "temperature": 0.1}, timeout=10)
    resp.raise_for_status()
    return json.loads(resp.json()["choices"][0]["message"]["content"])

@app.route("/monitor", methods=["POST"])
def start_monitoring():
    data = request.get_json()
    call_id = data.get("call_id")
    monitored_calls[call_id] = {"agent": data.get("agent"), "customer": data.get("customer"), "transcript_chunks": [], "sentiment_scores": [], "escalated": False}
    return jsonify({"status": "monitoring", "call_id": call_id}), 200

@app.route("/transcript", methods=["POST"])
def receive_transcript():
    data = request.get_json()
    call_id = data.get("call_id")
    text = data.get("text", "")
    speaker = data.get("speaker", "customer")
    call = monitored_calls.get(call_id)
    if not call: return jsonify({"error": "Call not monitored"}), 404
    call["transcript_chunks"].append({"speaker": speaker, "text": text, "time": time.time()})
    if speaker == "customer":
        has_trigger = any(w in text.lower() for w in TRIGGER_WORDS)
        try:
            analysis = analyze_sentiment(text)
            call["sentiment_scores"].append(analysis.get("score", 0))
            should_escalate = analysis.get("escalate", False) or has_trigger
        except Exception:
            should_escalate = has_trigger
        if should_escalate and not call["escalated"]:
            call["escalated"] = True
            escalation = {"call_id": call_id, "trigger": text[:100], "agent": call["agent"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
            escalations.append(escalation)
            if SUPERVISOR_NUMBER:
                try:
                    requests.post("https://api.telnyx.com/v2/messages", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                        json={"from": SUPERVISOR_NUMBER, "to": SUPERVISOR_NUMBER, "text": f"ESCALATION: Call {call_id} - Customer upset: '{text[:80]}'"}, timeout=10)
                except Exception: pass
            return jsonify({"status": "escalated", "analysis": analysis if 'analysis' in dir() else {}}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/calls/<call_id>/sentiment", methods=["GET"])
def call_sentiment(call_id):
    call = monitored_calls.get(call_id)
    if not call: return jsonify({"error": "Not found"}), 404
    scores = call["sentiment_scores"]
    avg = sum(scores) / max(len(scores), 1)
    trend = "improving" if len(scores) > 2 and scores[-1] > scores[0] else "declining" if len(scores) > 2 and scores[-1] < scores[0] else "stable"
    return jsonify({"call_id": call_id, "avg_sentiment": round(avg, 2), "trend": trend, "escalated": call["escalated"], "chunks": len(call["transcript_chunks"])}), 200

@app.route("/escalations", methods=["GET"])
def list_escalations():
    return jsonify({"escalations": escalations[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "monitoring": len(monitored_calls), "escalations": len(escalations)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
