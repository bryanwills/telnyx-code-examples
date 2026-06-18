#!/usr/bin/env python3
"""E-Learning Course Narrator — upload course content (lessons, quizzes),
AI structures into audio modules with pacing cues and quiz prompts,
TTS narrates each module, stores in Cloud Storage with a manifest."""

import os, json, uuid, requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TTS_MODEL = os.getenv("TTS_MODEL", "telnyx/tts")
BUCKET_NAME = os.getenv("BUCKET_NAME", "elearning")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "alloy")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

courses = {}


def inference(messages, max_tokens=4000):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def tts_generate(text, voice=None):
    resp = requests.post(f"{API}/ai/generate", headers=HEADERS, json={
        "model": TTS_MODEL, "voice": voice or DEFAULT_VOICE,
        "text": text, "output_format": "mp3"
    }, timeout=60)
    resp.raise_for_status()
    return resp.content


def upload_to_storage(key, data, content_type="audio/mpeg"):
    resp = requests.put(
        f"https://storage.telnyx.com/{BUCKET_NAME}/{key}",
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": content_type},
        data=data, timeout=60
    )
    resp.raise_for_status()
    return f"https://storage.telnyx.com/{BUCKET_NAME}/{key}"


@app.route("/courses/create", methods=["POST"])
def create_course():
    """Create a narrated e-learning course from text content.

    AI structures content into modules, adds quiz prompts and pacing,
    TTS narrates each module, stores audio + manifest in Cloud Storage.
    """
    data = request.get_json() or {}
    title = data.get("title", "Untitled Course")
    content = data.get("content", "")
    voice = data.get("voice", DEFAULT_VOICE)
    include_quizzes = data.get("include_quizzes", True)

    if not content:
        return jsonify({"error": "Provide 'content' text"}), 400

    course_id = f"course-{uuid.uuid4().hex[:8]}"
    courses[course_id] = {
        "id": course_id, "title": title, "status": "structuring",
        "voice": voice, "modules": [], "manifest": {},
        "total_audio_bytes": 0, "created_at": datetime.utcnow().isoformat()
    }

    # Step 1: AI structures content into narrated modules
    try:
        quiz_instruction = ""
        if include_quizzes:
            quiz_instruction = "After each module, include a 'Quiz Check' section with 2-3 questions the learner should pause and consider."

        modules_raw = inference([
            {"role": "system", "content": f"""Structure this educational content into narrated audio modules.

For each module, return JSON array with objects:
- "module_number": int
- "module_title": string
- "learning_objectives": [string] (2-3 per module)
- "narration": string (the text to read aloud — conversational, encouraging, with natural transitions)
- "quiz_prompt": string (pause-and-think questions, if applicable)
- "estimated_minutes": float

{quiz_instruction}

Guidelines:
- Speak to the learner directly ("you'll learn...", "notice how...")
- Add recap transitions between modules
- Keep each module under 5 minutes of narration (~750 words)
- Start each module with objectives, end with a summary"""},
            {"role": "user", "content": content[:12000]}
        ], max_tokens=4000)
        modules = json.loads(modules_raw)
    except json.JSONDecodeError:
        modules = [{"module_number": 1, "module_title": "Full Content", "narration": content[:3000], "learning_objectives": [], "estimated_minutes": 5}]
    except Exception as e:
        courses[course_id]["status"] = "failed"
        courses[course_id]["error"] = str(e)
        return jsonify(courses[course_id]), 500

    # Step 2: TTS narrate each module
    courses[course_id]["status"] = "narrating"
    manifest_modules = []

    for mod in modules:
        narration = mod.get("narration", "")
        quiz = mod.get("quiz_prompt", "")
        full_text = narration
        if quiz:
            full_text += f"\n\nNow, let's check your understanding.\n\n{quiz}"

        try:
            audio = tts_generate(full_text, voice=voice)
            module_data = {
                "number": mod.get("module_number", 0),
                "title": mod.get("module_title", ""),
                "learning_objectives": mod.get("learning_objectives", []),
                "estimated_minutes": mod.get("estimated_minutes", 0),
                "has_quiz": bool(quiz),
                "audio_bytes": len(audio),
                "word_count": len(full_text.split())
            }

            # Upload to Cloud Storage
            try:
                key = f"{course_id}/module-{module_data['number']:02d}.mp3"
                url = upload_to_storage(key, audio)
                module_data["storage_url"] = url
            except Exception as e:
                module_data["storage_error"] = str(e)

            courses[course_id]["modules"].append(module_data)
            courses[course_id]["total_audio_bytes"] += len(audio)
            manifest_modules.append({
                "module": module_data["number"],
                "title": module_data["title"],
                "objectives": module_data["learning_objectives"],
                "duration_est": module_data["estimated_minutes"],
                "file": f"module-{module_data['number']:02d}.mp3"
            })
        except Exception as e:
            courses[course_id]["modules"].append({
                "number": mod.get("module_number", 0),
                "title": mod.get("module_title", ""),
                "error": str(e)
            })

    # Upload course manifest
    manifest = {
        "course_id": course_id,
        "title": title,
        "voice": voice,
        "total_modules": len(manifest_modules),
        "modules": manifest_modules,
        "generated_at": datetime.utcnow().isoformat()
    }
    courses[course_id]["manifest"] = manifest
    try:
        manifest_json = json.dumps(manifest, indent=2).encode()
        upload_to_storage(f"{course_id}/manifest.json", manifest_json, "application/json")
    except Exception:
        pass

    courses[course_id]["status"] = "complete"
    courses[course_id]["completed_at"] = datetime.utcnow().isoformat()

    return jsonify({
        "course_id": course_id,
        "title": title,
        "status": "complete",
        "modules": len(courses[course_id]["modules"]),
        "total_audio_mb": round(courses[course_id]["total_audio_bytes"] / 1048576, 2),
        "total_est_minutes": sum(m.get("estimated_minutes", 0) for m in modules),
        "voice": voice
    }), 201


@app.route("/courses/<course_id>", methods=["GET"])
def get_course(course_id):
    course = courses.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    return jsonify(course)


@app.route("/courses", methods=["GET"])
def list_courses():
    return jsonify({"courses": [{
        "id": c["id"], "title": c["title"], "status": c["status"],
        "modules": len(c["modules"]), "created_at": c["created_at"]
    } for c in courses.values()]})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "total_courses": len(courses), "version": "1.0.0"})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
