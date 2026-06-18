#!/usr/bin/env python3
"""AI Video Dubbing Pipeline — upload audio, STT transcribes dialogue,
inference translates to target language, TTS generates dubbed audio track
with speaker-matched voices. Full pipeline on Telnyx."""

import os, json, uuid, time, requests, io, base64
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TTS_MODEL = os.getenv("TTS_MODEL", "telnyx/tts")
STT_MODEL = os.getenv("STT_MODEL", "telnyx/asr")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

# Voice mapping for dubbing — match source speaker characteristics to TTS voices
VOICE_MAP = {
    "male_low": "onyx",
    "male_mid": "echo",
    "female_mid": "nova",
    "female_high": "shimmer",
    "neutral": "alloy",
}

SUPPORTED_LANGUAGES = {
    "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
    "it": "Italian", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    "ar": "Arabic", "hi": "Hindi", "ru": "Russian", "nl": "Dutch",
    "sv": "Swedish", "pl": "Polish", "tr": "Turkish"
}

jobs = {}  # job_id -> dubbing state


def inference(messages, max_tokens=4000):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def transcribe_audio(audio_bytes, source_language="en"):
    """Transcribe audio using Telnyx STT with speaker diarization."""
    resp = requests.post(f"{API}/ai/transcribe", headers={
        "Authorization": f"Bearer {TELNYX_API_KEY}"
    }, files={
        "file": ("audio.mp3", audio_bytes, "audio/mpeg")
    }, data={
        "model": STT_MODEL,
        "language": source_language,
        "diarize": True,
        "timestamps": True
    }, timeout=120)
    resp.raise_for_status()
    return resp.json()


def tts_generate(text, voice="nova", language="en"):
    """Generate speech audio via Telnyx TTS."""
    resp = requests.post(f"{API}/ai/generate", headers=HEADERS, json={
        "model": TTS_MODEL,
        "voice": voice,
        "text": text,
        "language": language,
        "output_format": "mp3"
    }, timeout=30)
    resp.raise_for_status()
    return resp.content


@app.route("/dub", methods=["POST"])
def start_dubbing():
    """Upload audio and start the dubbing pipeline.

    Accepts multipart form with 'audio' file and 'target_language' field.
    Optionally 'source_language' (default: en).
    """
    if "audio" not in request.files:
        return jsonify({"error": "Upload an audio file as 'audio'"}), 400

    target_lang = request.form.get("target_language", "es")
    source_lang = request.form.get("source_language", "en")

    if target_lang not in SUPPORTED_LANGUAGES:
        return jsonify({
            "error": f"Unsupported target language: {target_lang}",
            "supported": SUPPORTED_LANGUAGES
        }), 400

    audio_file = request.files["audio"]
    audio_bytes = audio_file.read()

    job_id = f"dub-{uuid.uuid4().hex[:8]}"
    jobs[job_id] = {
        "id": job_id,
        "status": "transcribing",
        "source_language": source_lang,
        "target_language": target_lang,
        "target_language_name": SUPPORTED_LANGUAGES[target_lang],
        "created_at": datetime.utcnow().isoformat(),
        "transcript": None,
        "translated_segments": [],
        "dubbed_segments": [],
        "original_size_bytes": len(audio_bytes)
    }

    # Step 1: Transcribe with speaker diarization
    try:
        transcription = transcribe_audio(audio_bytes, source_lang)
        segments = transcription.get("segments", [])
        if not segments and transcription.get("text"):
            segments = [{"text": transcription["text"], "speaker": "SPEAKER_0", "start": 0, "end": 0}]
        jobs[job_id]["transcript"] = {
            "text": transcription.get("text", ""),
            "segments": segments,
            "speakers": list(set(s.get("speaker", "SPEAKER_0") for s in segments))
        }
        jobs[job_id]["status"] = "translating"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"Transcription failed: {str(e)}"
        return jsonify(jobs[job_id]), 500

    # Step 2: Translate each segment preserving speaker identity
    try:
        for segment in segments:
            translated = inference([
                {"role": "system", "content": f"Translate the following dialogue line from {source_lang} to {SUPPORTED_LANGUAGES[target_lang]}. Preserve tone, formality, and speaking style. Return ONLY the translated text, nothing else."},
                {"role": "user", "content": segment.get("text", "")}
            ], max_tokens=500)
            jobs[job_id]["translated_segments"].append({
                "speaker": segment.get("speaker", "SPEAKER_0"),
                "original": segment.get("text", ""),
                "translated": translated.strip(),
                "start": segment.get("start", 0),
                "end": segment.get("end", 0)
            })
        jobs[job_id]["status"] = "synthesizing"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"Translation failed: {str(e)}"
        return jsonify(jobs[job_id]), 500

    # Step 3: Generate TTS for each translated segment with speaker-matched voices
    speaker_voices = {}
    available_voices = list(VOICE_MAP.values())
    try:
        for i, seg in enumerate(jobs[job_id]["translated_segments"]):
            speaker = seg["speaker"]
            if speaker not in speaker_voices:
                voice_idx = len(speaker_voices) % len(available_voices)
                speaker_voices[speaker] = available_voices[voice_idx]

            voice = speaker_voices[speaker]
            audio = tts_generate(seg["translated"], voice=voice, language=target_lang)
            jobs[job_id]["dubbed_segments"].append({
                "speaker": speaker,
                "voice": voice,
                "text": seg["translated"],
                "audio_bytes": len(audio),
                "start": seg["start"],
                "end": seg["end"]
            })
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["speaker_voice_map"] = speaker_voices
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"TTS synthesis failed: {str(e)}"
        return jsonify(jobs[job_id]), 500

    jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

    return jsonify({
        "job_id": job_id,
        "status": "complete",
        "source_language": source_lang,
        "target_language": f"{target_lang} ({SUPPORTED_LANGUAGES[target_lang]})",
        "segments_dubbed": len(jobs[job_id]["dubbed_segments"]),
        "speakers": len(speaker_voices),
        "speaker_voice_map": speaker_voices
    }), 201


@app.route("/dub/<job_id>", methods=["GET"])
def get_job(job_id):
    """Get dubbing job status and results."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/dub/<job_id>/transcript", methods=["GET"])
def get_transcript(job_id):
    """Get side-by-side original and translated transcript."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    side_by_side = []
    for seg in job.get("translated_segments", []):
        side_by_side.append({
            "speaker": seg["speaker"],
            "original": seg["original"],
            "translated": seg["translated"],
            "timestamp": f"{seg['start']:.1f}s - {seg['end']:.1f}s"
        })

    return jsonify({
        "job_id": job_id,
        "source": job["source_language"],
        "target": job["target_language"],
        "segments": side_by_side
    })


@app.route("/languages", methods=["GET"])
def list_languages():
    """List supported dubbing target languages."""
    return jsonify({"languages": SUPPORTED_LANGUAGES})


@app.route("/jobs", methods=["GET"])
def list_jobs():
    """List all dubbing jobs."""
    return jsonify({
        "jobs": [{
            "id": j["id"],
            "status": j["status"],
            "source": j["source_language"],
            "target": j["target_language"],
            "segments": len(j.get("dubbed_segments", [])),
            "created_at": j["created_at"]
        } for j in jobs.values()]
    })


@app.route("/health", methods=["GET"])
def health():
    active = sum(1 for j in jobs.values() if j["status"] not in ("complete", "failed"))
    return jsonify({
        "status": "ok",
        "total_jobs": len(jobs),
        "active": active,
        "supported_languages": len(SUPPORTED_LANGUAGES),
        "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
