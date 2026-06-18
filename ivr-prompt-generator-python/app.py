#!/usr/bin/env python3
"""IVR Prompt Generator — generate professional IVR/phone system prompts.
AI writes caller-friendly scripts from business descriptions, TTS renders
in multiple voices, test via live Telnyx call playback."""

import os, json, uuid, requests
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()
app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MAIN_NUMBER = os.getenv("MAIN_NUMBER")
CONNECTION_ID = os.getenv("CONNECTION_ID")
AI_MODEL = os.getenv("AI_MODEL", "moonshotai/Kimi-K2.6")
TTS_MODEL = os.getenv("TTS_MODEL", "telnyx/tts")
BUCKET_NAME = os.getenv("BUCKET_NAME", "ivr-prompts")
API = "https://api.telnyx.com/v2"
HEADERS = {"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}

PROMPT_TYPES = {
    "greeting": "Main greeting when caller first connects",
    "menu": "Press 1 for X, Press 2 for Y options menu",
    "hold": "On-hold message with wait time estimate",
    "voicemail": "After-hours voicemail greeting",
    "transfer": "Please hold while we transfer your call",
    "closed": "We're currently closed, our hours are...",
    "holiday": "Holiday closure announcement",
    "queue": "All agents are busy, your call is important...",
}

prompt_sets = {}


def inference(messages, max_tokens=2000):
    resp = requests.post(f"{API}/ai/chat/completions", headers=HEADERS, json={
        "model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def tts_generate(text, voice="nova"):
    resp = requests.post(f"{API}/ai/generate", headers=HEADERS, json={
        "model": TTS_MODEL, "voice": voice, "text": text, "output_format": "mp3"
    }, timeout=30)
    resp.raise_for_status()
    return resp.content


def telnyx_post(path, payload):
    resp = requests.post(f"{API}/{path}", headers=HEADERS, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def upload_to_storage(key, data):
    resp = requests.put(
        f"https://storage.telnyx.com/{BUCKET_NAME}/{key}",
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "audio/mpeg"},
        data=data, timeout=60
    )
    resp.raise_for_status()
    return f"https://storage.telnyx.com/{BUCKET_NAME}/{key}"


@app.route("/prompts/generate", methods=["POST"])
def generate_prompts():
    """Generate a full IVR prompt set for a business.

    AI writes caller-friendly scripts, TTS renders each prompt.
    """
    data = request.get_json() or {}
    business_name = data.get("business_name", "")
    business_type = data.get("business_type", "")
    hours = data.get("hours", "Monday-Friday 9am-5pm")
    departments = data.get("departments", ["Sales", "Support", "Billing"])
    voice = data.get("voice", "nova")
    prompt_types = data.get("prompt_types", list(PROMPT_TYPES.keys()))

    if not business_name:
        return jsonify({"error": "Provide 'business_name'"}), 400

    set_id = f"ivr-{uuid.uuid4().hex[:8]}"
    prompt_sets[set_id] = {
        "id": set_id, "business": business_name, "status": "writing",
        "prompts": [], "created_at": datetime.utcnow().isoformat()
    }

    # Step 1: AI writes all prompts
    try:
        dept_list = ", ".join(departments)
        prompts_raw = inference([
            {"role": "system", "content": f"""Write professional IVR phone prompts for a business.

Business: {business_name} ({business_type})
Hours: {hours}
Departments: {dept_list}

For each prompt type, return JSON array with objects:
- "type": the prompt type
- "script": the exact words to speak (natural, professional, concise)
- "estimated_seconds": how long it takes to speak

Guidelines:
- Warm but efficient — callers hate long prompts
- Greeting under 10 seconds
- Menu options: keep to 4-5 max, most popular first
- Hold messages: acknowledge the wait, give useful info
- Always offer a callback or voicemail escape

Write these prompt types: {', '.join(prompt_types)}"""},
            {"role": "user", "content": f"Generate IVR prompts for {business_name}"}
        ])
        prompts = json.loads(prompts_raw)
    except json.JSONDecodeError:
        prompts = [{"type": "greeting", "script": prompts_raw[:200], "estimated_seconds": 8}]
    except Exception as e:
        prompt_sets[set_id]["status"] = "failed"
        prompt_sets[set_id]["error"] = str(e)
        return jsonify(prompt_sets[set_id]), 500

    # Step 2: TTS render each prompt
    prompt_sets[set_id]["status"] = "rendering"
    for prompt_data in prompts:
        script = prompt_data.get("script", "")
        try:
            audio = tts_generate(script, voice=voice)
            result = {
                "type": prompt_data.get("type", "unknown"),
                "script": script,
                "voice": voice,
                "audio_bytes": len(audio),
                "estimated_seconds": prompt_data.get("estimated_seconds", 0)
            }
            try:
                key = f"{set_id}/{prompt_data['type']}.mp3"
                url = upload_to_storage(key, audio)
                result["storage_url"] = url
            except Exception as e:
                result["storage_error"] = str(e)

            prompt_sets[set_id]["prompts"].append(result)
        except Exception as e:
            prompt_sets[set_id]["prompts"].append({
                "type": prompt_data.get("type"), "error": str(e)
            })

    prompt_sets[set_id]["status"] = "complete"
    prompt_sets[set_id]["completed_at"] = datetime.utcnow().isoformat()

    return jsonify({
        "set_id": set_id,
        "business": business_name,
        "prompts_generated": len(prompt_sets[set_id]["prompts"]),
        "voice": voice,
        "prompts": [{
            "type": p["type"],
            "script": p.get("script", "")[:100] + "..." if len(p.get("script", "")) > 100 else p.get("script", ""),
            "seconds": p.get("estimated_seconds", 0)
        } for p in prompt_sets[set_id]["prompts"] if "audio_bytes" in p]
    }), 201


@app.route("/prompts/<set_id>/preview", methods=["POST"])
def preview_prompt(set_id):
    """Call a phone number and play a specific prompt for live preview."""
    prompt_set = prompt_sets.get(set_id)
    if not prompt_set:
        return jsonify({"error": "Prompt set not found"}), 404

    data = request.get_json() or {}
    phone = data.get("phone", "")
    prompt_type = data.get("type", "greeting")

    if not phone:
        return jsonify({"error": "Provide 'phone' to call"}), 400

    prompt = None
    for p in prompt_set["prompts"]:
        if p.get("type") == prompt_type:
            prompt = p
            break

    if not prompt:
        return jsonify({"error": f"Prompt type '{prompt_type}' not found in this set"}), 404

    try:
        result = telnyx_post("calls", {
            "connection_id": CONNECTION_ID,
            "to": phone,
            "from": MAIN_NUMBER,
            "client_state": json.dumps({
                "action": "preview",
                "set_id": set_id,
                "script": prompt["script"]
            }).encode().hex()
        })
        return jsonify({
            "status": "calling",
            "phone": phone,
            "prompt_type": prompt_type,
            "script": prompt["script"],
            "call_id": result.get("data", {}).get("call_control_id")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/webhooks/voice", methods=["POST"])
def handle_voice():
    payload = request.get_json()
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    ep = event.get("payload", {})
    call_id = ep.get("call_control_id", "")

    if event_type == "call.answered":
        client_state = {}
        try:
            raw = ep.get("client_state", "")
            if raw:
                client_state = json.loads(bytes.fromhex(raw).decode())
        except Exception:
            pass

        if client_state.get("action") == "preview":
            script = client_state.get("script", "This is a test prompt.")
            try:
                telnyx_post(f"calls/{call_id}/actions/speak", {
                    "payload": script,
                    "voice": "nova",
                    "language": "en-US"
                })
            except Exception:
                pass

    elif event_type == "call.speak.ended":
        try:
            telnyx_post(f"calls/{call_id}/actions/hangup", {})
        except Exception:
            pass

    return jsonify({"status": "ok"}), 200


@app.route("/prompts/<set_id>", methods=["GET"])
def get_prompt_set(set_id):
    ps = prompt_sets.get(set_id)
    if not ps:
        return jsonify({"error": "Not found"}), 404
    return jsonify(ps)


@app.route("/prompt-types", methods=["GET"])
def get_prompt_types():
    return jsonify({"types": PROMPT_TYPES})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "total_sets": len(prompt_sets), "version": "1.0.0"})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
