#!/usr/bin/env python3
"""AI Content Translator — upload any audio (podcast, meeting, lecture),
STT transcribes in source language, inference translates, TTS generates
dubbed audio in target language. Returns translated audio + aligned transcript."""

import os, json, uuid, time, requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TTS_MODEL = os.getenv("TTS_MODEL", "telnyx/tts")
STT_MODEL = os.getenv("STT_MODEL", "telnyx/asr")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

LANGUAGES = {
    "en": {"name": "English", "voice": "nova"},
    "es": {"name": "Spanish", "voice": "nova"},
    "fr": {"name": "French", "voice": "nova"},
    "de": {"name": "German", "voice": "onyx"},
    "pt": {"name": "Portuguese", "voice": "nova"},
    "ja": {"name": "Japanese", "voice": "nova"},
    "ko": {"name": "Korean", "voice": "nova"},
    "zh": {"name": "Chinese", "voice": "nova"},
    "ar": {"name": "Arabic", "voice": "onyx"},
    "hi": {"name": "Hindi", "voice": "nova"},
    "it": {"name": "Italian", "voice": "nova"},
}

translations = {}


def inference(messages, max_tokens=4000):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def transcribe(audio_bytes, language="en"):
    resp = requests.post(f"{API}/ai/transcribe", headers={
        "Authorization": f"Bearer {TELNYX_API_KEY}"
    }, files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
    data={"model": STT_MODEL, "language": language, "timestamps": True},
    timeout=120)
    resp.raise_for_status()
    return resp.json()


def tts_generate(text, voice="nova", language="en"):
    resp = requests.post(f"{API}/ai/generate", headers=HEADERS, json={
        "model": TTS_MODEL, "voice": voice, "text": text,
        "language": language, "output_format": "mp3"
    }, timeout=30)
    resp.raise_for_status()
    return resp.content


@app.route("/translate", methods=["POST"])
def translate_content():
    """Upload audio and translate to target language with TTS output.

    Multipart form: 'audio' file, 'source' language code, 'target' language code.
    Pipeline: STT → translate → TTS.
    """
    if "audio" not in request.files:
        return jsonify({"error": "Upload audio file as 'audio'"}), 400

    source = request.form.get("source", "en")
    target = request.form.get("target", "es")

    if target not in LANGUAGES:
        return jsonify({"error": f"Unsupported language: {target}", "supported": list(LANGUAGES.keys())}), 400

    audio_bytes = request.files["audio"].read()
    job_id = f"tr-{uuid.uuid4().hex[:8]}"

    translations[job_id] = {
        "id": job_id, "status": "processing",
        "source": source, "target": target,
        "created_at": datetime.utcnow().isoformat(),
        "original_transcript": "", "translated_transcript": "",
        "segments": [], "audio_generated": False
    }

    # Step 1: Transcribe
    try:
        result = transcribe(audio_bytes, source)
        original_text = result.get("text", "")
        translations[job_id]["original_transcript"] = original_text
    except Exception as e:
        translations[job_id]["status"] = "failed"
        translations[job_id]["error"] = str(e)
        return jsonify(translations[job_id]), 500

    if not original_text.strip():
        translations[job_id]["status"] = "failed"
        translations[job_id]["error"] = "No speech detected in audio"
        return jsonify(translations[job_id]), 400

    # Step 2: Translate with context preservation
    try:
        target_name = LANGUAGES[target]["name"]
        source_name = LANGUAGES.get(source, {}).get("name", source)
        translated = inference([
            {"role": "system", "content": f"Translate the following {source_name} text to {target_name}. Preserve meaning, tone, and natural speech patterns. This will be read aloud, so make it sound natural when spoken. Return only the translation."},
            {"role": "user", "content": original_text}
        ])
        translations[job_id]["translated_transcript"] = translated.strip()
    except Exception as e:
        translations[job_id]["status"] = "failed"
        translations[job_id]["error"] = f"Translation failed: {str(e)}"
        return jsonify(translations[job_id]), 500

    # Step 3: Generate TTS in target language
    try:
        voice = LANGUAGES[target]["voice"]
        # Split into chunks for long content (TTS may have length limits)
        text = translations[job_id]["translated_transcript"]
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)] if len(text) > 1000 else [text]

        total_audio_bytes = 0
        for i, chunk in enumerate(chunks):
            audio = tts_generate(chunk, voice=voice, language=target)
            total_audio_bytes += len(audio)
            translations[job_id]["segments"].append({
                "index": i,
                "text": chunk,
                "audio_bytes": len(audio)
            })

        translations[job_id]["audio_generated"] = True
        translations[job_id]["total_audio_bytes"] = total_audio_bytes
    except Exception as e:
        translations[job_id]["status"] = "partial"
        translations[job_id]["error"] = f"TTS failed (transcript still available): {str(e)}"
        return jsonify(translations[job_id]), 200

    translations[job_id]["status"] = "complete"
    translations[job_id]["completed_at"] = datetime.utcnow().isoformat()

    return jsonify({
        "job_id": job_id,
        "status": "complete",
        "source": f"{source} ({source_name})",
        "target": f"{target} ({target_name})",
        "original_length": len(original_text),
        "translated_length": len(translations[job_id]["translated_transcript"]),
        "audio_segments": len(translations[job_id]["segments"]),
        "original_transcript": original_text[:500] + ("..." if len(original_text) > 500 else ""),
        "translated_transcript": translations[job_id]["translated_transcript"][:500] + ("..." if len(translations[job_id]["translated_transcript"]) > 500 else "")
    }), 201


@app.route("/translate/<job_id>", methods=["GET"])
def get_translation(job_id):
    """Get translation job with full side-by-side transcripts."""
    job = translations.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/languages", methods=["GET"])
def list_languages():
    return jsonify({"languages": {k: v["name"] for k, v in LANGUAGES.items()}})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "total_translations": len(translations),
        "supported_languages": len(LANGUAGES),
        "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
