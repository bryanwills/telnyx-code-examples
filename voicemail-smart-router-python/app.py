#!/usr/bin/env python3
"""AI Voicemail Smart Router — transcribe voicemails, classify intent, and route to the right channel via Telnyx STT + AI Inference."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "zai-org/GLM-5.2")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
STT_URL = "https://api.telnyx.com/v2/ai/audio/transcriptions"
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
voicemails = {}

SYSTEM_PROMPT = """You are a voicemail classification engine. Analyze the voicemail transcript and classify it into one of these categories:

- urgent: system outage, emergency, deadline, legal threat, anything needing immediate attention
- billing: invoice questions, payment issues, pricing inquiries, refund requests
- support: technical problems, bugs, how-to questions, product issues
- sales: new business inquiries, pricing for new accounts, partnership requests
- spam: robocalls, scams, promotional offers, irrelevant content
- routine: general messages, callbacks, check-ins, non-urgent inquiries

Also assign:
- confidence (0.0 to 1.0): how confident you are in the classification
- priority (high, medium, low): urgency level
- reason (string): one sentence explaining why you chose this category
- suggested_action (string): what should happen with this voicemail

Return JSON only:
{
  "category": "urgent" | "billing" | "support" | "sales" | "spam" | "routine",
  "confidence": 0.0,
  "priority": "high" | "medium" | "low",
  "reason": "...",
  "suggested_action": "..."
}"""

ROUTING_MAP = {
    "urgent": {"route": "slack", "destination": "#oncall-alerts"},
    "billing": {"route": "email", "destination": "billing@company.com"},
    "support": {"route": "ticket", "destination": "support-queue"},
    "sales": {"route": "crm", "destination": "sales-leads"},
    "spam": {"route": "blocklist", "destination": "archive"},
    "routine": {"route": "digest", "destination": "daily-digest"},
}

def call_inference(messages, max_tokens=4000):
    """Try primary model, fall back to secondary if it fails or times out."""
    for model in [AI_MODEL, FALLBACK_MODEL]:
        try:
            resp = requests.post(INFERENCE_URL,
                headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2},
                timeout=90)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"].get("content")
            if content is None:
                continue
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                content = content.rsplit("```", 1)[0]
                content = content.strip()
            return content, model
        except Exception:
            app.logger.warning("model %s failed, trying fallback", model)
            continue
    raise ValueError("all models failed")

def transcribe_audio(file_bytes, filename):
    """Send audio file to Telnyx STT API and return the transcript."""
    resp = requests.post(STT_URL,
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}"},
        files={"file": (filename, file_bytes, "audio/wav")},
        data={"model": "distil-whisper/distil-large-v2", "response_format": "json"},
        timeout=120)
    if not resp.ok:
        app.logger.error("STT failed: %s %s", resp.status_code, resp.text[:300])
    resp.raise_for_status()
    return resp.json().get("text", "")

def classify_and_route(transcript, caller_number=None):
    """Classify the voicemail transcript and determine the route."""
    prompt = f"Classify this voicemail:\n\n\"{transcript[:6000]}\""
    result_str, model_used = call_inference([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    result = json.loads(result_str)
    category = result.get("category", "routine")
    routing = ROUTING_MAP.get(category, ROUTING_MAP["routine"])
    result["route"] = routing["route"]
    result["routed_to"] = routing["destination"]
    result["routing_status"] = "pending"
    result["model_used"] = model_used
    # If urgent and Slack webhook is configured, send alert
    if category == "urgent" and SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={
                "text": f"URGENT VOICEMAIL from {caller_number or 'unknown'}:\n{transcript[:500]}"
            }, timeout=10)
            result["routing_status"] = "delivered"
        except Exception:
            result["routing_status"] = "delivery_failed"
    elif category == "spam" and caller_number:
        result["routing_status"] = "blocklisted"
    elif category != "urgent":
        result["routing_status"] = "queued"
    return result

@app.route("/voicemails/transcript", methods=["POST"])
def process_transcript():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    transcript = data.get("transcript", "").strip()
    if not transcript:
        return jsonify({"error": "transcript field is required"}), 400
    caller_number = data.get("caller_number")
    try:
        result = classify_and_route(transcript, caller_number)
        vm_id = f"vm-{int(time.time())}"
        result["id"] = vm_id
        result["transcript"] = transcript
        result["caller_number"] = caller_number
        result["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        voicemails[vm_id] = result
        return jsonify(result), 201
    except json.JSONDecodeError:
        return jsonify({"raw": result_str}), 200
    except Exception:
        app.logger.exception("voicemail classification failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/voicemails/process", methods=["POST"])
def process_audio():
    if "file" not in request.files:
        return jsonify({"error": "file field is required (upload an audio file)"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "no file provided"}), 400
    caller_number = request.form.get("caller_number")
    try:
        file_bytes = file.read()
        transcript = transcribe_audio(file_bytes, file.filename)
        if not transcript.strip():
            return jsonify({"error": "transcription returned empty text", "transcript": ""}), 422
        result = classify_and_route(transcript, caller_number)
        vm_id = f"vm-{int(time.time())}"
        result["id"] = vm_id
        result["transcript"] = transcript
        result["caller_number"] = caller_number
        result["source"] = f"audio:{file.filename}"
        result["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        voicemails[vm_id] = result
        return jsonify(result), 201
    except json.JSONDecodeError:
        return jsonify({"raw": result_str}), 200
    except Exception:
        app.logger.exception("audio voicemail processing failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/voicemails", methods=["GET"])
def list_voicemails():
    category = request.args.get("category")
    results = list(voicemails.values())[-50:]
    if category:
        results = [v for v in results if v.get("category") == category]
    return jsonify({"voicemails": results}), 200

@app.route("/voicemails/<vm_id>", methods=["GET"])
def get_voicemail(vm_id):
    vm = voicemails.get(vm_id)
    if not vm:
        return jsonify({"error": "voicemail not found"}), 404
    return jsonify(vm), 200

@app.route("/routes", methods=["GET"])
def list_routes():
    results = []
    for vid, v in list(voicemails.items())[-50:]:
        results.append({
            "id": vid,
            "category": v.get("category"),
            "route": v.get("route"),
            "routed_to": v.get("routed_to"),
            "routing_status": v.get("routing_status"),
            "priority": v.get("priority"),
            "generated_at": v.get("generated_at"),
        })
    return jsonify({"routes": results}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "voicemails": len(voicemails),
        "primary_model": AI_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "version": "1.0.0",
    }), 200

if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
