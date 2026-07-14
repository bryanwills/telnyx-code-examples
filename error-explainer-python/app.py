#!/usr/bin/env python3
"""AI Error Explainer — paste a stack trace, get a root-cause hypothesis and suggested fix via Telnyx AI Inference."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
analyses = {}

def call_inference(messages, max_tokens=4000):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=40)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"].get("content")
    if content is None:
        raise ValueError("model returned no content (try a larger max_tokens or a non-reasoning model)")
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content
        content = content.rsplit("```", 1)[0]
        content = content.strip()
    return content

def build_explain_prompt(stack_trace, language=None, context=None):
    lang_line = f" Language: {language}." if language else ""
    ctx_line = f" Context: {context}" if context else ""
    return f"""You are a senior software engineer diagnosing an error. Analyze this stack trace and return a structured diagnosis.{lang_line}{ctx_line}

Stack trace:
{stack_trace[:6000]}

Return JSON with these fields:
- root_cause (string): the most likely root cause, one or two sentences
- severity (string): one of "low", "medium", "high", "critical"
- confidence (float): 0.0 to 1.0 — how confident you are in the diagnosis
- likely_culprit (string): the file, function, or line that is the probable source
- suggested_fix (string): a concrete recommended fix, actionable
- fix_snippet (string): a short code snippet showing the corrected line(s), or null if not applicable
- related_errors (array of strings): other error types that commonly co-occur
- prevention (string): one-sentence tip to prevent this class of error in the future"""

@app.route("/explain", methods=["POST"])
def explain_error():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    stack_trace = data.get("stack_trace", "")
    if not stack_trace.strip():
        return jsonify({"error": "stack_trace field is required"}), 400
    language = data.get("language")
    context = data.get("context")
    prompt = build_explain_prompt(stack_trace, language, context)
    try:
        result = call_inference([
            {"role": "system", "content": "You are a senior software engineer who diagnoses errors from stack traces. Return JSON only."},
            {"role": "user", "content": prompt},
        ])
        analysis = json.loads(result)
        analysis_id = f"ex-{int(time.time())}"
        analysis["id"] = analysis_id
        analysis["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        analysis["language"] = language
        analyses[analysis_id] = analysis
        return jsonify(analysis), 200
    except json.JSONDecodeError:
        return jsonify({"raw": result}), 200
    except Exception:
        app.logger.exception("error explanation failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/analyses", methods=["GET"])
def list_analyses():
    results = list(analyses.values())[-50:]
    return jsonify({"analyses": results}), 200

@app.route("/analyses/<analysis_id>", methods=["GET"])
def get_analysis(analysis_id):
    analysis = analyses.get(analysis_id)
    if not analysis:
        return jsonify({"error": "analysis not found"}), 404
    return jsonify(analysis), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "analyses": len(analyses), "version": "1.0.0"}), 200

if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
