#!/usr/bin/env python3
"""AI Call Center Quality Scorer — automatically score agent performance from call recordings on compliance, empathy, resolution, and talk-to-listen ratio."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
scorecards = []

SCORECARD_PROMPT = """Score this call center interaction. Return JSON with:
- agent_name (string, if identifiable)
- greeting_score (1-10): proper greeting, name used
- compliance_score (1-10): disclosures, hold notifications, recording consent
- empathy_score (1-10): acknowledgment, tone, patience
- resolution_score (1-10): problem solved, clear next steps
- talk_ratio (float): estimated agent talk vs listen ratio (0.0-1.0)
- hold_time_mentioned (boolean)
- escalation_needed (boolean)
- prohibited_phrases (list): any forbidden language used
- coaching_notes (list of 3 specific improvement suggestions)
- overall_score (1-10)
- summary (2 sentences)
Be specific and constructive."""

def call_inference(messages, max_tokens=600):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/score", methods=["POST"])
def score_call():
    data = request.get_json()
    transcript = data.get("transcript", "")
    if not transcript:
        return jsonify({"error": "transcript required"}), 400
    try:
        result = call_inference([{"role": "system", "content": SCORECARD_PROMPT}, {"role": "user", "content": transcript}])
        scorecard = json.loads(result)
        scorecard["scored_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        scorecard["call_id"] = data.get("call_id", f"CALL-{int(time.time())}")
        scorecards.append(scorecard)
        return jsonify(scorecard), 200
    except json.JSONDecodeError:
        return jsonify({"raw_analysis": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/score/batch", methods=["POST"])
def batch_score():
    data = request.get_json()
    transcripts = data.get("transcripts", [])
    results = []
    for t in transcripts[:10]:
        try:
            result = call_inference([{"role": "system", "content": SCORECARD_PROMPT}, {"role": "user", "content": t.get("transcript", "")}])
            sc = json.loads(result)
            sc["call_id"] = t.get("call_id", f"CALL-{int(time.time())}")
            scorecards.append(sc)
            results.append(sc)
        except Exception:
            results.append({"call_id": t.get("call_id"), "error": "scoring failed"})
    return jsonify({"results": results}), 200

@app.route("/scorecards", methods=["GET"])
def list_scorecards():
    return jsonify({"scorecards": scorecards[-50:]}), 200

@app.route("/scorecards/summary", methods=["GET"])
def summary():
    if not scorecards: return jsonify({"message": "No scorecards yet"}), 200
    recent = scorecards[-20:]
    avg = lambda key: round(sum(s.get(key, 0) for s in recent) / len(recent), 1)
    return jsonify({"count": len(recent), "avg_overall": avg("overall_score"), "avg_empathy": avg("empathy_score"),
        "avg_compliance": avg("compliance_score"), "avg_resolution": avg("resolution_score")}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "scorecards": len(scorecards)}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
