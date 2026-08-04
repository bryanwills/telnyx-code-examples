#!/usr/bin/env python3
"""Multi-Character Narrator — paste a dialogue script with speaker labels,
assign each speaker a distinct Telnyx Ultra voice, render every line in
parallel, and stitch the per-line audio into one continuous MP3."""

import os
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

load_dotenv()

app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TTS_ENDPOINT = "https://api.telnyx.com/v2/text-to-speech/speech"
HEADERS = {
    "Authorization": f"Bearer {TELNYX_API_KEY}",
    "Content-Type": "application/json",
}

DEFAULT_VOICE_MAP = {
    "Narrator": "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f",  # Clara
    "Bob": "Telnyx.Ultra.00967b2f-88a6-4a31-8153-110a92134b9f",  # Asher
    "Alice": "Telnyx.Ultra.00a77add-48d5-4ef6-8157-71e5437b282d",  # Callie
    "Carol": "Telnyx.Ultra.2747b6cf-fa34-460c-97db-267566918881",  # Allie
}
FALLBACK_VOICE = "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f"  # Clara
MAX_WORKERS = 8

VOICE_DISPLAY_NAMES = {
    "Telnyx.Ultra.00967b2f-88a6-4a31-8153-110a92134b9f": "Asher (Ultra, M, en)",
    "Telnyx.Ultra.00a77add-48d5-4ef6-8157-71e5437b282d": "Callie (Ultra, F, en)",
    "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f": "Clara (Ultra, F, en-US)",
    "Telnyx.Ultra.0d42f0f6-c019-4082-b250-1c16133d1c82": "Howard (Ultra, M, en-US)",
    "Telnyx.Ultra.2747b6cf-fa34-460c-97db-267566918881": "Allie (Ultra, F, en-US)",
    "Telnyx.Ultra.3faa81ae-d3d8-4ab1-9e44-e50e46d33c30": "Jasper (Ultra, M, en-GB)",
    "Telnyx.Ultra.01fd7d67-d2a0-4e4e-8c48-42611c71a926": "Skyler (Ultra, M, en)",
    "Telnyx.Ultra.3f04e815-3260-4f50-8fd9-af9c657be4c2": "Arvin (Ultra, M, en)",
}

RECOMMENDED_VOICES = [
    {
        "id": "Telnyx.Ultra.00967b2f-88a6-4a31-8153-110a92134b9f",
        "name": "Asher",
        "gender": "Male",
        "language": "en",
        "model": "Ultra",
        "use_case": "Voice Assistants & Media",
        "sound_profile": "Smooth, dynamic, podcaster-style tone",
    },
    {
        "id": "Telnyx.Ultra.00a77add-48d5-4ef6-8157-71e5437b282d",
        "name": "Callie",
        "gender": "Female",
        "language": "en",
        "model": "Ultra",
        "use_case": "Coaching & Onboarding",
        "sound_profile": "High energy, encouraging, friendly tone",
    },
    {
        "id": "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f",
        "name": "Clara",
        "gender": "Female",
        "language": "en-US",
        "model": "Ultra",
        "use_case": "General Purpose IVR/AI",
        "sound_profile": "Clear, standard US accent, versatile pacing",
    },
    {
        "id": "Telnyx.Ultra.0d42f0f6-c019-4082-b250-1c16133d1c82",
        "name": "Howard",
        "gender": "Male",
        "language": "en-US",
        "model": "Ultra",
        "use_case": "Conversational Agents",
        "sound_profile": "Deep, reassuring, highly trustworthy",
    },
    {
        "id": "Telnyx.Ultra.2747b6cf-fa34-460c-97db-267566918881",
        "name": "Allie",
        "gender": "Female",
        "language": "en-US",
        "model": "Ultra",
        "use_case": "Casual & Interactive AI",
        "sound_profile": "Conversational flow, natural pauses",
    },
    {
        "id": "Telnyx.Ultra.3faa81ae-d3d8-4ab1-9e44-e50e46d33c30",
        "name": "Jasper",
        "gender": "Male",
        "language": "en-GB",
        "model": "Ultra",
        "use_case": "Finance & Healthcare",
        "sound_profile": "Calm, authoritative, precise delivery",
    },
    {
        "id": "Telnyx.Ultra.01fd7d67-d2a0-4e4e-8c48-42611c71a926",
        "name": "Skyler",
        "gender": "Neutral",
        "language": "en",
        "model": "Ultra",
        "use_case": "Modern Brand Voice",
        "sound_profile": "Casual, tech-forward, friendly vibe",
    },
    {
        "id": "Telnyx.Ultra.3f04e815-3260-4f50-8fd9-af9c657be4c2",
        "name": "Arvin",
        "gender": "Male",
        "language": "en",
        "model": "Ultra",
        "use_case": "Navigation & Directives",
        "sound_profile": "Steady, clear cadence for detailed guidance",
    },
]

DEFAULT_EMOTION_MAP = {
    "Narrator": "calm",
    "Cassius": "determined",
    "Caesar": "surprised",
    "Brutus": "apologetic",
    "Mark Antony": "angry",
    "Odysseus": "confident",
    "Trojan Guard": "hesitant",
    "King Priam": "confident",
    "Greek Soldier": "determined",
    "Demeter": "frustrated",
    "Hades": "calm",
    "Persephone": "apologetic",
    "Hermes": "calm",
    "Creon": "angry",
    "Antigone": "determined",
    "Ismene": "scared",
    "Hera": "confident",
    "Athena": "confident",
    "Aphrodite": "affectionate",
    "Paris": "hesitant",
}
NEUTRAL_EMOTION = "neutral"
SSML_EMOTIONS = [
    "neutral",
    "angry",
    "excited",
    "content",
    "sad",
    "scared",
    "happy",
    "enthusiastic",
    "curious",
    "calm",
    "grateful",
    "affectionate",
    "sarcastic",
    "surprised",
    "confident",
    "hesitant",
    "apologetic",
    "determined",
    "frustrated",
    "disappointed",
]

_telnyx_voices_cache = {"data": None, "fetched_at": 0}

DEFAULT_SCRIPT = """Cassius:
This is our moment. Rome cannot survive under one ruler. Stay focused.

Caesar:
What is happening? Why are you all surrounding me?

Brutus:
I am sorry, Caesar. This is not personal. I believe it is what Rome needs.

Caesar:
Brutus, even you? I never thought you would betray me.

Narrator:
The conspirators strike Caesar.

Caesar:
Then this is the end.

Cassius:
It is over. Rome is free.

Mark Antony:
Look at what you have done. The greatest leader Rome has ever known is gone.

Brutus:
We did not act out of hate. We acted because we believed Rome deserved a future without a tyrant.

Mark Antony:
History will decide whether you saved Rome or destroyed it."""

SAMPLE_SCRIPTS = {
    "Julius Caesar — the Ides of March": DEFAULT_SCRIPT,
}

projects = {}
_started_at = time.time()


def _start_ttl_cleanup(store, ttl_seconds=3600, interval=300):
    def _cleanup():
        while True:
            time.sleep(interval)
            cutoff = time.time() - ttl_seconds
            expired = [
                k
                for k, v in store.items()
                if isinstance(v, dict) and v.get("_ts", time.time()) < cutoff
            ]
            for k in expired:
                store.pop(k, None)

    threading.Thread(target=_cleanup, daemon=True).start()


_start_ttl_cleanup(projects)


def parse_script(script_text):
    """Parse a multi-line script into ordered lines.

    Each input line is split on the first colon. Lines without a label
    inherit the previous speaker. Blank lines are skipped.
    """
    lines = []
    current_speaker = None
    for raw in script_text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if ":" in stripped:
            speaker, text = stripped.split(":", 1)
            speaker = speaker.strip()
            text = text.strip()
            current_speaker = speaker
        else:
            speaker = current_speaker
            text = stripped
        if not speaker or not text:
            continue
        lines.append({"speaker": speaker, "text": text, "order": len(lines)})
    return lines


def resolve_voices(override):
    """Merge user-supplied speaker->voice overrides on top of the defaults."""
    merged = dict(DEFAULT_VOICE_MAP)
    if isinstance(override, dict):
        for k, v in override.items():
            if isinstance(v, str) and v:
                merged[k] = v
    return merged


def render_line(line, voice, emotion="neutral"):
    """Render one line via Telnyx Ultra TTS (REST, binary_output for honest TTFB).

    If emotion is set (not "neutral"), the line is wrapped with an inline SSML
    emotion tag and sent with text_type=ssml. Ultra interprets the rest of the
    emotional subtext from the text itself.
    """
    text = line["text"]
    text_type = "text"
    if emotion and emotion != "neutral" and emotion in SSML_EMOTIONS:
        text = f'<emotion value="{emotion}" />{text}'
        text_type = "ssml"
    body = {
        "text": text,
        "voice": voice,
        "output_type": "binary_output",
        "text_type": text_type,
    }
    started = time.time()
    try:
        with requests.post(
            TTS_ENDPOINT, headers=HEADERS, json=body, stream=True, timeout=60
        ) as r:
            r.raise_for_status()
            first_chunk_at = None
            audio = bytearray()
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    if first_chunk_at is None:
                        first_chunk_at = time.time()
                    audio.extend(chunk)
        ttfb_ms = int((first_chunk_at - started) * 1000) if first_chunk_at else None
        total_ms = int((time.time() - started) * 1000)
        return {
            "order": line["order"],
            "speaker": line["speaker"],
            "voice": voice,
            "emotion": emotion,
            "text": line["text"],
            "audio": bytes(audio),
            "ttfb_ms": ttfb_ms,
            "total_ms": total_ms,
            "error": None,
        }
    except requests.HTTPError as e:
        return {
            "order": line["order"],
            "speaker": line["speaker"],
            "voice": voice,
            "emotion": emotion,
            "text": line["text"],
            "audio": b"",
            "ttfb_ms": None,
            "total_ms": int((time.time() - started) * 1000),
            "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
        }
    except requests.RequestException as e:
        return {
            "order": line["order"],
            "speaker": line["speaker"],
            "voice": voice,
            "emotion": emotion,
            "text": line["text"],
            "audio": b"",
            "ttfb_ms": None,
            "total_ms": int((time.time() - started) * 1000),
            "error": f"network: {str(e)[:200]}",
        }


@app.route("/narrate", methods=["POST"])
def narrate():
    """Render a multi-character script to a single stitched MP3."""
    data = request.get_json(silent=True) or {}
    script = data.get("script", "")
    title = data.get("title", "Untitled Scene")
    voice_override = data.get("voices", {})
    emotion_override = data.get("emotions", {})

    if not script:
        return jsonify({"error": "Missing required field: 'script'"}), 400

    lines = parse_script(script)
    if not lines:
        return jsonify({"error": "No speakable lines found in script"}), 400

    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    voice_map = resolve_voices(voice_override)
    emotion_map = dict(DEFAULT_EMOTION_MAP)
    if isinstance(emotion_override, dict):
        for k, v in emotion_override.items():
            if isinstance(v, str) and v in SSML_EMOTIONS:
                emotion_map[k] = v
    speakers = sorted({line["speaker"] for line in lines})

    rendered = [None] * len(lines)
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(lines))) as pool:
        futures = {
            pool.submit(
                render_line,
                line,
                voice_map.get(line["speaker"], FALLBACK_VOICE),
                emotion_map.get(line["speaker"], NEUTRAL_EMOTION),
            ): line
            for line in lines
        }
        for fut in as_completed(futures):
            res = fut.result()
            rendered[res["order"]] = res

    ordered = [r for r in rendered if r is not None]
    failed = [r for r in ordered if r["error"] is not None]
    successful = [r for r in ordered if r["error"] is None and r["audio"]]

    stitched = b"".join(r["audio"] for r in successful)
    project_id = f"narr-{uuid.uuid4().hex[:8]}"
    projects[project_id] = {
        "id": project_id,
        "title": title,
        "lines": ordered,
        "audio": stitched,
        "_ts": time.time(),
    }

    response = {
        "project_id": project_id,
        "title": title,
        "lines_rendered": len(successful),
        "lines_failed": len(failed),
        "speakers": speakers,
        "voice_map": voice_map,
        "emotion_map": emotion_map,
        "voice_display_names": {
            v: VOICE_DISPLAY_NAMES.get(v, v) for v in voice_map.values()
        },
        "per_line_voices": [
            voice_map.get(r["speaker"], FALLBACK_VOICE) for r in ordered
        ],
        "per_line_emotions": [r["emotion"] for r in ordered],
        "per_line_speakers": [r["speaker"] for r in ordered],
        "per_line_text": [r["text"] for r in ordered],
        "total_ms": sum(r["total_ms"] or 0 for r in ordered),
        "per_line_ttfb_ms": [r["ttfb_ms"] for r in ordered],
        "audio_url": f"/audio/{project_id}.mp3",
    }
    if failed:
        response["errors"] = [
            {"order": r["order"], "speaker": r["speaker"], "error": r["error"]}
            for r in failed
        ]
    return jsonify(response), 200


@app.route("/audio/<project_id>.mp3", methods=["GET"])
def audio(project_id):
    """Stream the stitched MP3 for a project."""
    project = projects.get(project_id)
    if not project:
        return jsonify({"error": "project not found"}), 404
    return Response(project["audio"], mimetype="audio/mpeg")


@app.route("/projects", methods=["GET"])
def list_projects():
    """List recent render projects (metadata only)."""
    return jsonify(
        {
            "projects": [
                {
                    "id": p["id"],
                    "title": p["title"],
                    "lines_rendered": sum(1 for r in p["lines"] if r["error"] is None),
                    "created_at": p["_ts"],
                }
                for p in projects.values()
            ]
        }
    )


@app.route("/samples", methods=["GET"])
def samples():
    """Return preset scripts for the demo UI."""
    return jsonify({"scripts": SAMPLE_SCRIPTS})


@app.route("/voices", methods=["GET"])
def voices():
    """Return the default voice map and display names for the demo UI."""
    return jsonify(
        {
            "default_voice_map": DEFAULT_VOICE_MAP,
            "display_names": VOICE_DISPLAY_NAMES,
            "fallback_voice": FALLBACK_VOICE,
        }
    )


@app.route("/recommended-voices", methods=["GET"])
def recommended_voices():
    """Return the curated list of 10 recommended Telnyx voices."""
    return jsonify({"voices": RECOMMENDED_VOICES})


@app.route("/emotions", methods=["GET"])
def emotions():
    """Return the list of Ultra SSML emotions and the default emotion map."""
    return jsonify(
        {
            "emotions": SSML_EMOTIONS,
            "default_emotion_map": DEFAULT_EMOTION_MAP,
        }
    )


@app.route("/preview", methods=["POST"])
def preview():
    """Render a short sample line in a given voice. Returns binary MP3."""
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500
    data = request.get_json(silent=True) or {}
    voice = data.get("voice", "")
    text = data.get("text", "Hello, this is a voice preview.")
    text_type = data.get("text_type", "text")
    if not voice:
        return jsonify({"error": "Missing required field: 'voice'"}), 400
    if len(text) > 300:
        text = text[:300]
    body = {
        "text": text,
        "voice": voice,
        "text_type": text_type,
        "output_type": "binary_output",
    }
    try:
        r = requests.post(TTS_ENDPOINT, headers=HEADERS, json=body, timeout=30)
        r.raise_for_status()
        return Response(r.content, mimetype="audio/mpeg")
    except requests.HTTPError as e:
        return jsonify(
            {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        ), 502
    except requests.RequestException as e:
        return jsonify({"error": f"network: {str(e)[:200]}"}), 502


@app.route("/telnyx-logo.svg", methods=["GET"])
def logo():
    """Serve the Telnyx logo SVG (green mark + cream wordmark) for the demo UI."""
    logo_path = os.path.join(os.path.dirname(__file__), "telnyx-logo.svg")
    try:
        with open(logo_path, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="image/svg+xml")
    except FileNotFoundError:
        return Response("", status=404)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "uptime_s": int(time.time() - _started_at)}), 200


PLAYER_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multi-Character Narrator — Telnyx</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #000;
    --panel: #0d0d0d;
    --panel-2: #161616;
    --border: #1f1f1f;
    --border-2: #2a2a2a;
    --text: #fafafa;
    --muted: #8a8a8a;
    --muted-2: #5a5a5a;
    --green: #00E3AA;
    --green-dim: #00B894;
    --cream: #F5F0E8;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
    font-size: 17px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
    min-height: 100vh;
  }
  .wrap { max-width: 1040px; margin: 0 auto; padding: 56px 24px 96px; }

  .brand {
    display: flex; align-items: center; gap: 12px; margin-bottom: 56px;
  }
  .brand .logo-svg {
    height: 32px; width: auto; display: block;
  }
  .brand .tag { color: var(--muted-2); font-size: 14px; font-weight: 400; }
  .brand .tag::before { content: '·'; margin: 0 10px; color: var(--muted-2); }

  h1 {
    font-size: 44px; font-weight: 700; letter-spacing: -0.03em;
    line-height: 1.1; margin: 0 0 16px; color: var(--cream);
  }
  .lede {
    font-size: 19px; color: var(--muted); margin: 0 0 40px;
    max-width: 720px; line-height: 1.5;
  }
  .lede strong { color: var(--text); font-weight: 500; }

  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
  }
  .panel-label {
    font-size: 12px; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--green);
    margin: 0 0 16px;
  }

  .samples {
    display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;
  }
  .chip {
    background: var(--panel-2); border: 1px solid var(--border-2);
    color: var(--muted); padding: 7px 14px; border-radius: 999px;
    font-size: 13px; font-weight: 500; cursor: pointer;
    transition: all 0.15s ease;
  }
  .chip:hover { color: var(--text); border-color: var(--green-dim); }
  .chip.active { background: var(--green); color: #000; border-color: var(--green); }

  textarea {
    width: 100%; box-sizing: border-box;
    font-family: 'JetBrains Mono', ui-monospace, Menlo, monospace;
    font-size: 15px; line-height: 1.6;
    padding: 20px; background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border-2); border-radius: 12px;
    min-height: 200px; resize: vertical;
    outline: none;
  }
  textarea:focus { border-color: var(--green-dim); }
  textarea::placeholder { color: var(--muted-2); }

  .actions {
    display: flex; align-items: center; gap: 20px; margin-top: 24px;
  }
  button.render {
    background: var(--green); color: #000;
    border: none; padding: 14px 28px; border-radius: 10px;
    font-size: 16px; font-weight: 600; cursor: pointer;
    transition: transform 0.1s ease, background 0.15s ease;
    font-family: inherit;
  }
  button.render:hover { background: #1BFFC2; }
  button.render:active { transform: translateY(1px); }
  button.render:disabled { background: #2a2a2a; color: #5a5a5a; cursor: default; }
  .hint { color: var(--muted-2); font-size: 14px; }

  .status {
    font-size: 15px; color: var(--muted); margin-top: 28px;
    display: flex; align-items: center; gap: 10px;
  }
  .status .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--muted-2); display: inline-block;
  }
  .status.working .dot { background: var(--green); animation: pulse 1s ease infinite; }
  .status.done .dot { background: var(--green); }
  .status.error .dot { background: #ff5a5a; }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
  }

  #result { margin-top: 36px; }
  .result-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 28px;
    animation: rise 0.3s ease;
  }
  @keyframes rise {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .scene-label {
    font-size: 12px; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--green);
    margin: 0 0 8px;
  }
  .scene-title {
    font-size: 22px; font-weight: 600; color: var(--cream);
    margin: 0 0 20px; letter-spacing: -0.01em;
  }
  audio {
    width: 100%; margin: 0 0 28px;
    border-radius: 10px;
  }
  audio::-webkit-media-controls-panel { background: #1a1a1a; }
  audio::-webkit-media-controls-current-time-display,
  audio::-webkit-media-controls-time-remaining-display { color: #ccc; }

  .cast {
    display: flex; flex-direction: column; gap: 0;
  }
  .cast-label {
    font-size: 12px; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--muted);
    margin: 0 0 14px;
  }
  .cast-row {
    display: grid; grid-template-columns: 140px 1fr;
    gap: 20px; padding: 14px 0;
    border-top: 1px solid var(--border);
    align-items: baseline;
  }
  .cast-row .speaker {
    font-weight: 600; color: var(--green); font-size: 16px;
  }
  .cast-row .voice {
    color: var(--muted); font-size: 15px;
  }
  .emotion-badge {
    display: inline-block; background: rgba(0,227,170,0.15);
    color: var(--green); padding: 2px 8px; border-radius: 4px;
    font-size: 12px; font-weight: 500; margin-left: 8px;
    text-transform: lowercase; letter-spacing: 0.02em;
  }
  .emotion-select {
    background: rgba(0,227,170,0.05) !important;
    border-color: rgba(0,227,170,0.3) !important;
  }
  .cast-row .line-text {
    grid-column: 1 / -1; color: var(--cream); font-size: 16px;
    line-height: 1.5; margin-top: 4px; opacity: 0.85;
  }

  .voice-picker {
    margin-top: 32px;
    padding-top: 28px;
    border-top: 1px solid var(--border);
  }
  .voice-picker-label {
    font-size: 12px; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--green);
    margin: 0 0 6px;
  }
  .voice-picker-hint {
    font-size: 14px; color: var(--muted-2); margin: 0 0 20px;
  }
  .speaker-row {
    display: grid; grid-template-columns: 120px 1fr; gap: 16px;
    padding: 16px 0; border-top: 1px solid var(--border);
    align-items: center;
  }
  .speaker-row .speaker-name {
    font-weight: 600; color: var(--green); font-size: 16px;
  }
  .voice-select-wrap {
    display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
  }
  select.voice-select {
    background: var(--bg); color: var(--text);
    border: 1px solid var(--border-2); border-radius: 8px;
    padding: 9px 12px; font-size: 14px; font-family: inherit;
    cursor: pointer; min-width: 240px;
    outline: none;
  }
  select.voice-select:focus { border-color: var(--green-dim); }
  select.voice-select option { background: #1a1a1a; color: var(--text); }
  .preview-btn {
    background: transparent; color: var(--green);
    border: 1px solid var(--border-2); padding: 8px 14px;
    border-radius: 8px; font-size: 13px; font-weight: 500;
    cursor: pointer; font-family: inherit;
    display: inline-flex; align-items: center; gap: 6px;
    transition: border-color 0.15s ease;
  }
  .preview-btn:hover { border-color: var(--green-dim); }
  .preview-btn:disabled { color: var(--muted-2); cursor: default; }
  .preview-btn.playing { border-color: var(--green); color: var(--green); }

  .err {
    color: #ff7a7a; font-size: 15px; margin-top: 16px;
    padding: 14px 16px; background: rgba(255,90,90,0.08);
    border: 1px solid rgba(255,90,90,0.2); border-radius: 10px;
  }

  .footer {
    margin-top: 64px; padding-top: 28px;
    border-top: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 16px;
  }
  .footer .left { color: var(--muted-2); font-size: 14px; }
  .footer a {
    color: var(--green); text-decoration: none; font-size: 15px;
    font-weight: 500; display: inline-flex; align-items: center; gap: 6px;
    border: 1px solid var(--border-2); padding: 10px 16px;
    border-radius: 10px; transition: border-color 0.15s ease;
  }
  .footer a:hover { border-color: var(--green-dim); }

  @media (max-width: 640px) {
    .wrap { padding: 32px 16px 64px; }
    h1 { font-size: 32px; }
    .lede { font-size: 17px; }
    .panel { padding: 20px; }
    .cast-row { grid-template-columns: 110px 1fr; gap: 12px; }
  }
</style>
</head>
<body>
<div class="wrap">

  <div class="brand">
    <img src="/telnyx-logo.svg" alt="Telnyx" class="logo-svg">
    <span class="tag">Voice AI</span>
  </div>

  <h1>Multi-Character Narrator</h1>
  <p class="lede">
    Paste a dialogue script, assign each character a <strong>Telnyx Ultra voice</strong>,
    and render the whole scene in parallel into one audio file.
    Built to show how one platform, one API key, and four distinct voices
    can replace the usual DAW + multi-vendor stitching workflow.
  </p>

  <div class="panel">
    <p class="panel-label">Your script</p>
    <textarea id="script" placeholder="Narrator: The scene opens with...&#10;Bob: Hi there.&#10;Alice: Welcome."></textarea>

    <div class="actions">
      <button id="render" class="render" onclick="render()">Render scene</button>
      <span class="hint">Format: <code>Speaker: text</code> — one line per character</span>
    </div>

    <div class="status" id="status">
      <span class="dot"></span>
      <span class="msg">Ready to render</span>
    </div>
  </div>

  <div id="result"></div>

  <div class="voice-picker" id="voice-picker" style="display:none">
    <p class="voice-picker-label">Cast your characters</p>
    <p class="voice-picker-hint">Speakers detected in your script. Pick a Telnyx voice and an emotion for each character, then render. Click <strong>▶</strong> to preview a voice with that emotion.</p>
    <div id="speaker-rows"></div>
  </div>

  <div class="footer">
    <div class="left">Powered by Telnyx Ultra TTS — sub-100ms TTFB, 36 languages, one voice platform.</div>
    <a href="https://github.com/team-telnyx/telnyx-code-examples/tree/main/multi-character-narrator-python" target="_blank" rel="noopener">
      View source →
    </a>
  </div>

</div>

<script>
const SAMPLES = __SAMPLE_SCRIPTS_JSON__;
const VOICE_DISPLAY = __VOICE_DISPLAY_JSON__;
const RECOMMENDED = __RECOMMENDED_VOICES_JSON__;
const EMOTIONS = __EMOTIONS_JSON__;
const DEFAULT_EMOTIONS = __DEFAULT_EMOTIONS_JSON__;

const scriptEl = document.getElementById('script');
const pickerEl = document.getElementById('voice-picker');
const speakerRowsEl = document.getElementById('speaker-rows');
const firstSample = Object.values(SAMPLES)[0];
scriptEl.value = firstSample || '';

let voiceAssignments = {};
let emotionAssignments = {};

function detectSpeakers() {
  const lines = scriptEl.value.split('\\n').map(l => l.trim()).filter(l => l && l.includes(':'));
  const speakers = [];
  const seen = new Set();
  for (const l of lines) {
    const sp = l.split(':')[0].trim();
    if (sp && !seen.has(sp)) { seen.add(sp); speakers.push(sp); }
  }
  if (speakers.length === 0) { pickerEl.style.display = 'none'; return; }
  pickerEl.style.display = 'block';
  speakerRowsEl.innerHTML = '';
  const defaultVoices = {"Narrator": RECOMMENDED[0].id, "Bob": RECOMMENDED[1].id, "Alice": RECOMMENDED[2].id, "Carol": RECOMMENDED[3].id};
  speakers.forEach(sp => {
    if (!voiceAssignments[sp]) {
      voiceAssignments[sp] = defaultVoices[sp] || RECOMMENDED[speakers.indexOf(sp) % RECOMMENDED.length].id;
    }
    if (!emotionAssignments[sp]) {
      emotionAssignments[sp] = DEFAULT_EMOTIONS[sp] || 'neutral';
    }
    const row = document.createElement('div');
    row.className = 'speaker-row';
    const nameSpan = document.createElement('div');
    nameSpan.className = 'speaker-name';
    nameSpan.textContent = sp;
    const selWrap = document.createElement('div');
    selWrap.className = 'voice-select-wrap';
    const sel = document.createElement('select');
    sel.className = 'voice-select';
    RECOMMENDED.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = `${v.name} — ${v.use_case} (${v.gender[0]}, ${v.language})`;
      if (v.id === voiceAssignments[sp]) opt.selected = true;
      sel.appendChild(opt);
    });
    sel.onchange = () => { voiceAssignments[sp] = sel.value; };
    const emoSel = document.createElement('select');
    emoSel.className = 'voice-select emotion-select';
    emoSel.style.minWidth = '160px';
    EMOTIONS.forEach(e => {
      const opt = document.createElement('option');
      opt.value = e;
      opt.textContent = e.charAt(0).toUpperCase() + e.slice(1);
      if (e === emotionAssignments[sp]) opt.selected = true;
      emoSel.appendChild(opt);
    });
    emoSel.onchange = () => { emotionAssignments[sp] = emoSel.value; };
    const prev = document.createElement('button');
    prev.className = 'preview-btn';
    prev.innerHTML = '▶ Preview';
    prev.onclick = () => playPreview(sel.value, emoSel.value, prev);
    selWrap.appendChild(sel);
    selWrap.appendChild(emoSel);
    selWrap.appendChild(prev);
    row.appendChild(nameSpan);
    row.appendChild(selWrap);
    speakerRowsEl.appendChild(row);
  });
}

let previewAudio = null;
let previewBtn = null;
function playPreview(voiceId, emotion, btn) {
  if (previewAudio) { previewAudio.pause(); previewAudio = null; if (previewBtn) previewBtn.classList.remove('playing'); }
  btn.classList.add('playing');
  btn.disabled = true;
  btn.textContent = '◌ Loading';
  let text = 'Hello, this is a voice preview from Telnyx.';
  if (emotion && emotion !== 'neutral') {
    text = `<emotion value="${emotion}" />${text}`;
  }
  const textType = (emotion && emotion !== 'neutral') ? 'ssml' : 'text';
  fetch('/preview', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({voice: voiceId, text: text, text_type: textType})
  }).then(r => r.blob()).then(blob => {
    const url = URL.createObjectURL(blob);
    previewAudio = new Audio(url);
    previewAudio.onended = () => { btn.classList.remove('playing'); btn.textContent = '▶ Preview'; btn.disabled = false; previewAudio = null; previewBtn = null; };
    previewAudio.play();
    previewBtn = btn;
    btn.textContent = '■ Stop';
  }).catch(e => { btn.classList.remove('playing'); btn.textContent = '▶ Preview'; btn.disabled = false; });
}

scriptEl.addEventListener('input', () => { detectSpeakers(); });
detectSpeakers();

function setStatus(state, msg) {
  const s = document.getElementById('status');
  s.className = 'status ' + state;
  s.querySelector('.msg').textContent = msg;
}
function resetStatus() {
  setStatus('', 'Ready to render');
  document.getElementById('result').innerHTML = '';
}

async function render() {
  const btn = document.getElementById('render');
  btn.disabled = true;
  setStatus('working', 'Rendering scene...');
  document.getElementById('result').innerHTML = '';
  try {
    const r = await fetch('/narrate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title: 'My scene', script: scriptEl.value, voices: voiceAssignments, emotions: emotionAssignments})
    });
    const j = await r.json();
    if (!r.ok) {
      setStatus('error', 'Error: ' + (j.error || 'unknown'));
      return;
    }
    if (j.lines_failed > 0) {
      setStatus('error', 'Scene rendered with ' + j.lines_failed + ' failed line(s)');
    } else {
      setStatus('done', 'Scene rendered');
    }
    renderResult(j);
  } catch (e) {
    setStatus('error', 'Network error: ' + e);
  } finally {
    btn.disabled = false;
  }
}

function renderResult(j) {
  const display = VOICE_DISPLAY || {};
  const voiceMap = j.voice_map || {};
  const emotionMap = j.emotion_map || {};
  const speakers = j.per_line_speakers || j.speakers || [];
  const texts = j.per_line_text || [];
  const voices = j.per_line_voices || [];
  const emotions = j.per_line_emotions || [];

  let html = '<div class="result-card">';
  html += '<p class="scene-label">Scene rendered</p>';
  html += '<p class="scene-title">' + escapeHtml(j.title || 'My scene') + '</p>';
  html += '<audio controls autoplay src="' + j.audio_url + '"></audio>';

  html += '<p class="cast-label">Cast</p>';
  html += '<div class="cast">';
  const seenSpeakers = new Set();
  for (let i = 0; i < speakers.length; i++) {
    const sp = speakers[i];
    const voice = voices[i] || voiceMap[sp] || '';
    const voiceName = display[voice] || voice;
    const emotion = emotions[i] || emotionMap[sp] || 'neutral';
    const text = texts[i] || '';
    if (!seenSpeakers.has(sp)) {
      seenSpeakers.add(sp);
      html += '<div class="cast-row">';
      html += '<span class="speaker">' + escapeHtml(sp) + '</span>';
      const emotionTag = (emotion && emotion !== 'neutral') ? ' <span class="emotion-badge">' + escapeHtml(emotion) + '</span>' : '';
      html += '<span class="voice">' + escapeHtml(voiceName) + emotionTag + '</span>';
      html += '</div>';
    }
    html += '<div class="cast-row">';
    html += '<span class="speaker" style="opacity:0.5">' + escapeHtml(sp) + '</span>';
    html += '<span class="line-text">' + escapeHtml(text) + '</span>';
    html += '</div>';
  }
  html += '</div>';

  if (j.errors && j.errors.length) {
    html += '<div class="err"><strong>Errors:</strong><br>';
    html += j.errors.map(e => 'Line ' + e.order + ' (' + e.speaker + '): ' + escapeHtml(e.error)).join('<br>');
    html += '</div>';
  }

  html += '</div>';
  document.getElementById('result').innerHTML = html;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
</script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    import json

    return (
        PLAYER_HTML.replace("__DEFAULT_SCRIPT__", DEFAULT_SCRIPT)
        .replace("__SAMPLE_SCRIPTS_JSON__", json.dumps(SAMPLE_SCRIPTS))
        .replace("__VOICE_DISPLAY_JSON__", json.dumps(VOICE_DISPLAY_NAMES))
        .replace("__RECOMMENDED_VOICES_JSON__", json.dumps(RECOMMENDED_VOICES))
        .replace("__EMOTIONS_JSON__", json.dumps(SSML_EMOTIONS))
        .replace("__DEFAULT_EMOTIONS_JSON__", json.dumps(DEFAULT_EMOTION_MAP))
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    app.run(debug=False, port=port)
