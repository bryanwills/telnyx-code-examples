#!/usr/bin/env python3
"""Podcast Episode Repurposer — feed a recorded episode, STT transcribes,
inference extracts key quotes and topics, TTS generates audiogram clips
with different voices, SMS distributes clips to subscriber list."""

import os, json, uuid, requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MAIN_NUMBER = os.getenv("MAIN_NUMBER")
MESSAGING_PROFILE_ID = os.getenv("MESSAGING_PROFILE_ID", "")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TTS_MODEL = os.getenv("TTS_MODEL", "telnyx/tts")
STT_MODEL = os.getenv("STT_MODEL", "telnyx/asr")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

CLIP_VOICES = ["nova", "onyx", "echo", "shimmer", "alloy"]
jobs = {}
subscribers = []  # list of E.164 phone numbers


def inference(messages, max_tokens=2000):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.4
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def transcribe(audio_bytes, language="en"):
    resp = requests.post(f"{API}/ai/transcribe", headers={
        "Authorization": f"Bearer {TELNYX_API_KEY}"
    }, files={"file": ("audio.mp3", audio_bytes, "audio/mpeg")},
    data={"model": STT_MODEL, "language": language, "timestamps": True, "diarize": True},
    timeout=120)
    resp.raise_for_status()
    return resp.json()


def tts_generate(text, voice="nova"):
    resp = requests.post(f"{API}/ai/generate", headers=HEADERS, json={
        "model": TTS_MODEL, "voice": voice, "text": text, "output_format": "mp3"
    }, timeout=30)
    resp.raise_for_status()
    return resp.content


def send_sms(to, text):
    try:
        requests.post(f"{API}/messages", headers=HEADERS, json={
            "from": MAIN_NUMBER, "to": to, "text": text,
            "messaging_profile_id": MESSAGING_PROFILE_ID
        }, timeout=10)
    except Exception as e:
        app.logger.error(f"SMS to {to} failed: {e}")


@app.route("/repurpose", methods=["POST"])
def repurpose_episode():
    """Upload a podcast episode audio file. Returns clips, quotes, and social posts.

    Pipeline: STT → AI extract quotes/topics → TTS audiogram clips → SMS distribution.
    """
    if "audio" not in request.files:
        return jsonify({"error": "Upload episode audio as 'audio'"}), 400

    episode_title = request.form.get("title", "Untitled Episode")
    audio_bytes = request.files["audio"].read()

    job_id = f"rep-{uuid.uuid4().hex[:8]}"
    jobs[job_id] = {
        "id": job_id, "title": episode_title, "status": "transcribing",
        "created_at": datetime.utcnow().isoformat(),
        "transcript": "", "quotes": [], "clips": [], "social_posts": [],
        "distribution": {"sent": 0, "failed": 0}
    }

    # Step 1: Transcribe
    try:
        result = transcribe(audio_bytes)
        transcript = result.get("text", "")
        jobs[job_id]["transcript"] = transcript
        jobs[job_id]["word_count"] = len(transcript.split())
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"Transcription failed: {str(e)}"
        return jsonify(jobs[job_id]), 500

    if not transcript.strip():
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = "No speech detected"
        return jsonify(jobs[job_id]), 400

    # Step 2: Extract quotable moments
    jobs[job_id]["status"] = "extracting"
    try:
        quotes_raw = inference([
            {"role": "system", "content": "Extract the 5 most quotable, shareable moments from this podcast transcript. For each quote, return JSON array with objects: {\"quote\": \"exact words under 280 chars\", \"context\": \"why this is interesting\", \"topic\": \"topic tag\", \"hook\": \"social media hook sentence\"}. Focus on surprising insights, strong opinions, and actionable advice."},
            {"role": "user", "content": transcript[:8000]}
        ])
        jobs[job_id]["quotes"] = json.loads(quotes_raw)
    except json.JSONDecodeError:
        jobs[job_id]["quotes"] = [{"quote": quotes_raw[:280], "context": "extracted", "topic": "general", "hook": "Listen to this:"}]
    except Exception as e:
        jobs[job_id]["error"] = f"Quote extraction failed: {str(e)}"

    # Step 3: Generate social posts
    try:
        social_raw = inference([
            {"role": "system", "content": f"Generate 3 social media posts promoting the podcast episode '{episode_title}'. Each should use a different quote/angle. Return JSON array with objects: {{\"platform\": \"twitter|linkedin|instagram\", \"text\": \"post text with emoji\", \"hashtags\": [\"tag1\"]}}. Twitter: punchy, under 280 chars. LinkedIn: professional insight. Instagram: conversational with emojis."},
            {"role": "user", "content": json.dumps(jobs[job_id]["quotes"][:3])}
        ])
        jobs[job_id]["social_posts"] = json.loads(social_raw)
    except Exception:
        pass

    # Step 4: Generate TTS audiogram clips for top quotes
    jobs[job_id]["status"] = "generating_clips"
    for i, quote in enumerate(jobs[job_id]["quotes"][:5]):
        try:
            voice = CLIP_VOICES[i % len(CLIP_VOICES)]
            clip_text = f"{quote.get('hook', 'From the show:')} {quote['quote']}"
            audio = tts_generate(clip_text, voice=voice)
            jobs[job_id]["clips"].append({
                "index": i,
                "quote": quote["quote"][:100],
                "voice": voice,
                "audio_bytes": len(audio),
                "clip_text": clip_text
            })
        except Exception as e:
            app.logger.error(f"Clip {i} TTS failed: {e}")

    # Step 5: Distribute via SMS to subscribers
    if subscribers and jobs[job_id]["quotes"]:
        best_quote = jobs[job_id]["quotes"][0]
        sms_text = f"🎙️ New episode: {episode_title}\n\n\"{best_quote['quote'][:200]}\"\n\nListen now!"
        for phone in subscribers:
            try:
                send_sms(phone, sms_text)
                jobs[job_id]["distribution"]["sent"] += 1
            except Exception:
                jobs[job_id]["distribution"]["failed"] += 1

    jobs[job_id]["status"] = "complete"
    jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

    return jsonify({
        "job_id": job_id,
        "status": "complete",
        "title": episode_title,
        "word_count": jobs[job_id].get("word_count", 0),
        "quotes_extracted": len(jobs[job_id]["quotes"]),
        "clips_generated": len(jobs[job_id]["clips"]),
        "social_posts": len(jobs[job_id]["social_posts"]),
        "sms_sent": jobs[job_id]["distribution"]["sent"]
    }), 201


@app.route("/repurpose/<job_id>", methods=["GET"])
def get_job(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/subscribers", methods=["POST"])
def add_subscriber():
    """Add a phone number to the SMS distribution list."""
    data = request.get_json() or {}
    phone = data.get("phone")
    if not phone:
        return jsonify({"error": "Provide 'phone' in E.164 format"}), 400
    if phone not in subscribers:
        subscribers.append(phone)
    return jsonify({"subscribers": len(subscribers), "added": phone})


@app.route("/subscribers", methods=["GET"])
def list_subscribers():
    return jsonify({"subscribers": [s[-4:] for s in subscribers], "total": len(subscribers)})


@app.route("/jobs", methods=["GET"])
def list_jobs():
    return jsonify({"jobs": [{
        "id": j["id"], "title": j["title"], "status": j["status"],
        "quotes": len(j["quotes"]), "clips": len(j["clips"]),
        "created_at": j["created_at"]
    } for j in jobs.values()]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok", "total_jobs": len(jobs),
        "subscribers": len(subscribers), "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
