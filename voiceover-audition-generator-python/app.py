#!/usr/bin/env python3
"""Voice-Over Audition Generator — submit a script, hear it read by every
available TTS voice with AI-scored best-fit recommendations. Compare voices
side by side. Delivers top picks via SMS to decision-makers."""

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
BUCKET_NAME = os.getenv("BUCKET_NAME", "voiceovers")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

ALL_VOICES = [
    {"id": "nova", "name": "Nova", "traits": "warm, approachable, female"},
    {"id": "onyx", "name": "Onyx", "traits": "deep, authoritative, male"},
    {"id": "echo", "name": "Echo", "traits": "natural, conversational, male"},
    {"id": "shimmer", "name": "Shimmer", "traits": "bright, energetic, female"},
    {"id": "alloy", "name": "Alloy", "traits": "neutral, clean, balanced"},
]

auditions = {}


def inference(messages, max_tokens=1000):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.4
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


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
        return True
    except Exception:
        return False


def upload_to_storage(key, data):
    resp = requests.put(
        f"https://storage.telnyx.com/{BUCKET_NAME}/{key}",
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "audio/mpeg"},
        data=data, timeout=60
    )
    resp.raise_for_status()
    return f"https://storage.telnyx.com/{BUCKET_NAME}/{key}"


@app.route("/auditions/create", methods=["POST"])
def create_audition():
    """Submit a script and get TTS auditions from every voice with AI scoring.

    Generates audio for all voices, AI ranks best fit based on script content,
    optionally SMS top picks to decision-makers.
    """
    data = request.get_json() or {}
    script = data.get("script", "")
    project = data.get("project", "Untitled")
    context = data.get("context", "")  # e.g., "luxury car commercial", "kids app tutorial"
    notify_phones = data.get("notify", [])

    if not script:
        return jsonify({"error": "Provide 'script' text"}), 400

    audition_id = f"aud-{uuid.uuid4().hex[:8]}"
    auditions[audition_id] = {
        "id": audition_id, "project": project, "status": "rendering",
        "script": script, "context": context,
        "voices": [], "ranking": [], "created_at": datetime.utcnow().isoformat()
    }

    # Step 1: Render all voices
    for voice_cfg in ALL_VOICES:
        try:
            audio = tts_generate(script, voice=voice_cfg["id"])
            voice_result = {
                "voice_id": voice_cfg["id"],
                "voice_name": voice_cfg["name"],
                "traits": voice_cfg["traits"],
                "audio_bytes": len(audio)
            }

            try:
                key = f"{audition_id}/{voice_cfg['id']}.mp3"
                url = upload_to_storage(key, audio)
                voice_result["storage_url"] = url
            except Exception as e:
                voice_result["storage_error"] = str(e)

            auditions[audition_id]["voices"].append(voice_result)
        except Exception as e:
            auditions[audition_id]["voices"].append({
                "voice_id": voice_cfg["id"],
                "voice_name": voice_cfg["name"],
                "error": str(e)
            })

    # Step 2: AI ranks voices for this script
    auditions[audition_id]["status"] = "scoring"
    try:
        voice_list = "\n".join([f"- {v['name']}: {v['traits']}" for v in ALL_VOICES])
        context_note = f"\nContext: {context}" if context else ""
        ranking_raw = inference([
            {"role": "system", "content": f"""You are a professional voice casting director. Rank these TTS voices for the given script.

Available voices:
{voice_list}
{context_note}

Evaluate each voice on:
1. Tone match (does the voice suit the content?)
2. Authority (does it convey the right level of credibility?)
3. Engagement (would the target audience want to keep listening?)
4. Pacing fit (does the voice's natural rhythm work for this script?)

Return JSON array ranked best to worst, each with:
{{"voice_id": "...", "rank": 1, "score": 85, "reasoning": "one sentence why", "best_for": "what type of content this voice excels at"}}"""},
            {"role": "user", "content": script}
        ])
        ranking = json.loads(ranking_raw)
        auditions[audition_id]["ranking"] = ranking
    except json.JSONDecodeError:
        auditions[audition_id]["ranking"] = [{"voice_id": "nova", "rank": 1, "score": 80, "reasoning": ranking_raw[:200]}]
    except Exception as e:
        auditions[audition_id]["ranking_error"] = str(e)

    # Step 3: SMS notify decision-makers with top pick
    if notify_phones and auditions[audition_id]["ranking"]:
        top = auditions[audition_id]["ranking"][0]
        sms_text = f"🎤 Voice audition for '{project}':\n\nTop pick: {top.get('voice_id', '?')} (score: {top.get('score', '?')}/100)\n{top.get('reasoning', '')}\n\n{len(ALL_VOICES)} voice samples ready for review."
        for phone in notify_phones:
            send_sms(phone, sms_text)

    auditions[audition_id]["status"] = "complete"
    auditions[audition_id]["completed_at"] = datetime.utcnow().isoformat()

    return jsonify({
        "audition_id": audition_id,
        "project": project,
        "status": "complete",
        "voices_rendered": len([v for v in auditions[audition_id]["voices"] if "audio_bytes" in v]),
        "top_pick": auditions[audition_id]["ranking"][0] if auditions[audition_id]["ranking"] else None,
        "full_ranking": auditions[audition_id]["ranking"]
    }), 201


@app.route("/auditions/<audition_id>", methods=["GET"])
def get_audition(audition_id):
    aud = auditions.get(audition_id)
    if not aud:
        return jsonify({"error": "Audition not found"}), 404
    return jsonify(aud)


@app.route("/auditions", methods=["GET"])
def list_auditions():
    return jsonify({"auditions": [{
        "id": a["id"], "project": a["project"], "status": a["status"],
        "voices": len(a["voices"]), "created_at": a["created_at"]
    } for a in auditions.values()]})


@app.route("/voices", methods=["GET"])
def list_voices():
    return jsonify({"voices": ALL_VOICES})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "total_auditions": len(auditions), "version": "1.0.0"})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
