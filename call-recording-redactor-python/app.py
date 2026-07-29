#!/usr/bin/env python3
"""AI Call Recording Redactor — transcribe call audio and redact PII (names, cards, SSNs, addresses, phones, emails) via Telnyx AI Inference."""
import os, json, time, requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
load_dotenv()
app = Flask(__name__)
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
INFERENCE_URL = "https://api.telnyx.com/v2/ai/chat/completions"
STT_URL = "https://api.telnyx.com/v2/ai/audio/transcriptions"
redactions = {}

SYSTEM_PROMPT = """You are a PII redaction engine. Analyze the transcript and redact all personally identifiable information (PII) by replacing each instance with a tagged placeholder.

PII types to redact:
- Names (person names) → [NAME]
- Credit card numbers → [CREDIT_CARD]
- SSN / national ID numbers → [SSN]
- Phone numbers → [PHONE]
- Email addresses → [EMAIL]
- Street addresses → [ADDRESS]
- Dates of birth → [DOB]
- Account numbers → [ACCOUNT_NUMBER]

Return JSON only with this shape:
{
  "redacted_transcript": "the full transcript with PII replaced by placeholders",
  "redactions": [
    {
      "type": "name",
      "original": "the original PII text",
      "redacted": "[NAME]",
      "count": 1
    }
  ],
  "items_redacted": 3,
  "pii_types_found": ["name", "credit_card"]
}

Rules:
- Preserve the original transcript structure and readability.
- Replace each PII instance with the appropriate placeholder.
- List each unique PII instance in the redactions array.
- If no PII is found, return the transcript unchanged with items_redacted: 0."""

def call_inference(messages, max_tokens=6000):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=120)
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

def transcribe_audio(file_bytes, filename, language=None):
    """Send audio file to Telnyx STT API and return the transcript."""
    data = {
        "model": "distil-whisper/distil-large-v2",
        "response_format": "json",
    }
    if language and language != "en-US":
        data["language"] = language
    resp = requests.post(STT_URL,
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}"},
        files={"file": (filename, file_bytes, "audio/wav")},
        data=data,
        timeout=60)
    if not resp.ok:
        app.logger.error("STT failed: %s %s", resp.status_code, resp.text[:300])
    resp.raise_for_status()
    return resp.json().get("text", "")

def redact_transcript(transcript):
    """Send transcript to AI Inference for PII redaction."""
    prompt = f"Redact all PII from this transcript:\n\n{transcript[:6000]}"
    result = call_inference([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    return json.loads(result)

@app.route("/redact", methods=["POST"])
def redact_text():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    transcript = data.get("transcript", "").strip()
    if not transcript:
        return jsonify({"error": "transcript field is required"}), 400
    try:
        result = redact_transcript(transcript)
        red_id = f"red-{int(time.time())}"
        result["id"] = red_id
        result["source"] = "text"
        result["original_transcript"] = transcript
        result["status"] = "done"
        result["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        redactions[red_id] = result
        return jsonify(result), 201
    except json.JSONDecodeError:
        return jsonify({"raw": result}), 200
    except Exception:
        app.logger.exception("redaction failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/redact/audio", methods=["POST"])
def redact_audio():
    if "file" not in request.files:
        return jsonify({"error": "file field is required (upload an audio file)"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "no file provided"}), 400
    language = request.form.get("language")
    try:
        file_bytes = file.read()
        app.logger.info("Transcribing %s (%d bytes), language=%s", file.filename, len(file_bytes), language)
        transcript = transcribe_audio(file_bytes, file.filename, language)
        if not transcript.strip():
            return jsonify({"error": "transcription returned empty text", "transcript": ""}), 422
        result = redact_transcript(transcript)
        red_id = f"red-{int(time.time())}"
        result["id"] = red_id
        result["source"] = f"audio:{file.filename}"
        result["original_transcript"] = transcript
        result["status"] = "done"
        result["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        redactions[red_id] = result
        return jsonify(result), 201
    except json.JSONDecodeError:
        return jsonify({"raw": result}), 200
    except Exception:
        app.logger.exception("audio redaction failed")
        return jsonify({"error": "internal error"}), 500

@app.route("/redactions", methods=["GET"])
def list_redactions():
    results = []
    for rid, r in list(redactions.items())[-50:]:
        results.append({
            "id": rid,
            "source": r.get("source"),
            "items_redacted": r.get("items_redacted", 0),
            "pii_types_found": r.get("pii_types_found", []),
            "status": r.get("status"),
            "generated_at": r.get("generated_at"),
        })
    return jsonify({"redactions": results}), 200

@app.route("/redactions/<red_id>", methods=["GET"])
def get_redaction(red_id):
    r = redactions.get(red_id)
    if not r:
        return jsonify({"error": "redaction not found"}), 404
    return jsonify(r), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "redactions": len(redactions), "version": "1.0.0"}), 200

if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
