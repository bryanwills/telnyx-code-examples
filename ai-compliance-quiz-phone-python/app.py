#!/usr/bin/env python3
"""AI Compliance Quiz Phone — employees call and take a compliance quiz. AI asks questions, evaluates answers, scores pass/fail, records completion."""
import os, json, time, requests, telnyx
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
client = telnyx.Telnyx(api_key=os.getenv("TELNYX_API_KEY"))
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
QUIZ_NUMBER = os.getenv("QUIZ_NUMBER")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
active_calls = {}
completions = []

QUIZ_QUESTIONS = [
    {"q": "Is it ever acceptable to share your login credentials with a coworker who needs urgent access?", "correct": "No — credentials should never be shared. The coworker should request their own access through IT."},
    {"q": "You receive an email from the CEO asking you to wire transfer $50,000 immediately. The email address looks slightly different. What do you do?", "correct": "Do not comply. Verify through a separate channel like phone call to the CEO's known number. This is likely a BEC (business email compromise) attack."},
    {"q": "A customer asks you to look up another customer's account information. They claim to be their spouse. What's the right action?", "correct": "Decline. Verify authorization through proper channels. Customer data requires explicit consent from the account holder."},
    {"q": "You find a USB drive in the parking lot. What should you do?", "correct": "Do not plug it into any computer. Turn it in to IT security. It could contain malware."},
    {"q": "Is it okay to discuss company financial results with friends before the public earnings call?", "correct": "No. This is insider information and sharing it violates securities law."},
]

def call_inference(messages, max_tokens=150):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=15)
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
        active_calls[ccid] = {"caller": data.get("from"), "question_idx": 0, "scores": [], "start": time.time()}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="Welcome to the quarterly compliance quiz. I'll ask 5 questions. Answer each one verbally. Let's begin.", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended" and call:
        idx = call["question_idx"]
        if idx < len(QUIZ_QUESTIONS):
            client.calls.actions.speak(ccid, payload=f"Question {idx+1}: {QUIZ_QUESTIONS[idx]['q']}", voice="female", language_code="en-US")
            call["question_idx"] = -1
        elif call["question_idx"] == -1:
            call["question_idx"] = idx
            client.calls.actions.gather(ccid, input_type="speech", end_silence_timeout_secs=3, timeout_secs=30, language_code="en-US")
        return jsonify({"status": "asking"}), 200
    elif event_type == "call.gather.ended" and call:
        speech = data.get("speech", {}).get("result", "")
        idx = call["question_idx"]
        if speech and idx < len(QUIZ_QUESTIONS):
            q = QUIZ_QUESTIONS[idx]
            grade = call_inference([{"role": "system", "content": f"Grade this compliance quiz answer. Correct answer: {q['correct']}. Return JSON: correct (boolean), score (0-10), feedback (1 sentence)."},
                {"role": "user", "content": speech}])
            try:
                result = json.loads(grade)
            except Exception:
                result = {"correct": False, "score": 5, "feedback": "Answer noted."}
            call["scores"].append(result)
            feedback = result.get("feedback", "")
            call["question_idx"] = idx + 1
            if idx + 1 < len(QUIZ_QUESTIONS):
                client.calls.actions.speak(ccid, payload=f"{feedback} Next question.", voice="female", language_code="en-US")
            else:
                total = sum(s.get("score", 0) for s in call["scores"])
                passed = total >= 35
                client.calls.actions.speak(ccid, payload=f"{feedback}. Quiz complete! Score: {total} out of 50. {'You passed!' if passed else 'Please retake the quiz after reviewing the compliance handbook.'}", voice="female", language_code="en-US")
        return jsonify({"status": "grading"}), 200
    elif event_type == "call.hangup":
        call = active_calls.pop(ccid, None)
        if call:
            total = sum(s.get("score", 0) for s in call.get("scores", []))
            completions.append({"caller": call["caller"], "score": total, "max": 50, "passed": total >= 35, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
        return jsonify({"status": "ended"}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/completions", methods=["GET"])
def list_completions():
    return jsonify({"completions": completions[-50:]}), 200

@app.route("/health", methods=["GET"])
def health():
    passed = sum(1 for c in completions if c.get("passed"))
    return jsonify({"status": "ok", "total": len(completions), "passed": passed}), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
