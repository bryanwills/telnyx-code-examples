#!/usr/bin/env python3
"""Telnyx Speech Translator — record your voice, transcribe it, translate it,
and hear it in another language. STT → Inference → TTS on one platform.

No phone, no database, no Cloud Storage, no AI Assistant. Three REST calls:
  1. POST /v2/ai/audio/transcriptions  (STT)
  2. POST /v2/ai/chat/completions      (translation via Inference)
  3. POST /v2/text-to-speech/speech    (TTS)

The browser never receives the API key.
"""

import io
import os
import time
import uuid
import threading

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, send_file

load_dotenv()

app = Flask(__name__)

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
if not TELNYX_API_KEY:
    print(
        "WARNING: TELNYX_API_KEY is not set — the app will start but API calls will fail."
    )

STT_ENDPOINT = "https://api.telnyx.com/v2/ai/audio/transcriptions"
STT_MODEL = os.getenv("STT_MODEL", "openai/whisper-large-v3-turbo")

INFERENCE_ENDPOINT = "https://api.telnyx.com/v2/ai/chat/completions"
TRANSLATION_MODEL = os.getenv("TRANSLATION_MODEL", "moonshotai/Kimi-K2.6")

TTS_ENDPOINT = "https://api.telnyx.com/v2/text-to-speech/speech"
TTS_VOICE = os.getenv("TTS_VOICE", "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f")
TTS_AUDIO_FORMAT = os.getenv("TTS_AUDIO_FORMAT", "mp3")

MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024
MAX_TRANSLATION_CHARS = 10000
MAX_TTS_CHARS = 3000
TEMP_FILE_TTL_SECONDS = int(os.getenv("TEMP_FILE_TTL_MINUTES", "30")) * 60

SUPPORTED_AUDIO_EXTS = {".webm", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}

TARGET_LANGUAGES = [
    "Spanish",
    "English",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Hindi",
    "Japanese",
]

LANGUAGE_BOOST_MAP = {
    "Spanish": "Spanish",
    "English": "English",
    "French": "French",
    "German": "German",
    "Italian": "Italian",
    "Portuguese": "Portuguese",
    "Hindi": "Hindi",
    "Japanese": "Japanese",
}

LANGUAGE_FILE_PREFIX = {
    "Spanish": "spanish",
    "English": "english",
    "French": "french",
    "German": "german",
    "Italian": "italian",
    "Portuguese": "portuguese",
    "Hindi": "hindi",
    "Japanese": "japanese",
}

_store = {}
_started_at = time.time()


def _start_ttl_cleanup(store, ttl_seconds, interval=300):
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


_start_ttl_cleanup(_store, TEMP_FILE_TTL_SECONDS)


def _safe_filename(name):
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def _today_str():
    return time.strftime("%Y-%m-%d")


# ─── STT ────────────────────────────────────────────────────────────────────


def _call_stt(audio_bytes, filename):
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in SUPPORTED_AUDIO_EXTS:
        ext = ".webm"
    upload_name = filename if ext in (filename or "") else f"audio{ext}"
    files = {"file": (upload_name, audio_bytes, "application/octet-stream")}
    data = {"model": STT_MODEL}
    resp = requests.post(
        STT_ENDPOINT,
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}"},
        files=files,
        data=data,
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()


# ─── Translation ────────────────────────────────────────────────────────────


def _call_translate(text, target_language):
    system_prompt = (
        f"You are a professional translator.\n\n"
        f"Translate the supplied text from its original language into {target_language}.\n\n"
        f"Requirements:\n"
        f"- Preserve the original meaning.\n"
        f"- Preserve names, numbers, technical terms, and formatting.\n"
        f"- Do not summarize.\n"
        f"- Do not explain the translation.\n"
        f"- Return only the translated text."
    )
    body = {
        "model": TRANSLATION_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 1000,
    }
    resp = requests.post(
        INFERENCE_ENDPOINT,
        headers={
            "Authorization": f"Bearer {TELNYX_API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not content:
        raise ValueError("Translation model returned empty content")
    return content.strip()


# ─── TTS ────────────────────────────────────────────────────────────────────


def _call_tts(text, target_language):
    voice_settings = {}
    boost = LANGUAGE_BOOST_MAP.get(target_language)
    if boost:
        voice_settings["language_boost"] = boost
    body = {
        "text": text,
        "voice": TTS_VOICE,
        "output_type": "binary_output",
    }
    if voice_settings:
        body["voice_settings"] = voice_settings
    resp = requests.post(
        TTS_ENDPOINT,
        headers={
            "Authorization": f"Bearer {TELNYX_API_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    if "audio" not in request.files:
        return jsonify({"error": "Missing required file upload: 'audio'"}), 400

    audio_file = request.files["audio"]
    audio_bytes = audio_file.read()
    if not audio_bytes:
        return jsonify({"error": "Audio file is empty"}), 400

    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        return jsonify(
            {"error": f"Audio file exceeds {MAX_AUDIO_SIZE_MB} MB limit"}
        ), 413

    filename = audio_file.filename or "audio.webm"
    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in SUPPORTED_AUDIO_EXTS:
        return jsonify(
            {
                "error": f"Unsupported file format: {ext}. Supported: {', '.join(sorted(SUPPORTED_AUDIO_EXTS))}"
            }
        ), 400

    started = time.time()
    try:
        result = _call_stt(audio_bytes, filename)
    except requests.HTTPError as e:
        return jsonify(
            {
                "error": f"STT failed: HTTP {e.response.status_code}: {e.response.text[:300]}"
            }
        ), 502
    except requests.RequestException as e:
        return jsonify({"error": f"STT network error: {str(e)[:200]}"}), 502

    duration_ms = int((time.time() - started) * 1000)
    transcript = result.get("text", "").strip()
    if not transcript:
        return jsonify({"error": "STT returned empty transcript"}), 502

    detected_language = result.get("language", "auto-detected")

    note_id = f"note-{uuid.uuid4().hex[:8]}"
    _store[note_id] = {
        "id": note_id,
        "transcript": transcript,
        "detected_language": detected_language,
        "model": STT_MODEL,
        "duration_ms": duration_ms,
        "created_at": time.time(),
        "_ts": time.time(),
    }

    return jsonify(
        {
            "note_id": note_id,
            "transcript": transcript,
            "detected_language": detected_language,
            "model": STT_MODEL,
            "duration_ms": duration_ms,
            "download_url": f"/notes/{note_id}/download",
        }
    ), 200


@app.route("/translate", methods=["POST"])
def translate():
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    data = request.get_json(silent=True) or {}
    source_text = data.get("source_text", "").strip()
    target_language = data.get("target_language", "Spanish")

    if not source_text:
        return jsonify({"error": "Missing required field: 'source_text'"}), 400
    if target_language not in TARGET_LANGUAGES:
        return jsonify(
            {
                "error": f"Unsupported target language: {target_language}. Supported: {', '.join(TARGET_LANGUAGES)}"
            }
        ), 400
    if len(source_text) > MAX_TRANSLATION_CHARS:
        return jsonify(
            {"error": f"Source text exceeds {MAX_TRANSLATION_CHARS} character limit"}
        ), 413

    try:
        translated_text = _call_translate(source_text, target_language)
    except requests.HTTPError as e:
        return jsonify(
            {
                "error": f"Translation failed: HTTP {e.response.status_code}: {e.response.text[:300]}"
            }
        ), 502
    except requests.RequestException as e:
        return jsonify({"error": f"Translation network error: {str(e)[:200]}"}), 502
    except ValueError as e:
        return jsonify({"error": f"Translation model error: {str(e)[:200]}"}), 502

    translation_id = f"trans-{uuid.uuid4().hex[:8]}"
    _store[translation_id] = {
        "id": translation_id,
        "source_text": source_text,
        "target_language": target_language,
        "translated_text": translated_text,
        "created_at": time.time(),
        "_ts": time.time(),
    }

    return jsonify(
        {
            "translation_id": translation_id,
            "source_text": source_text,
            "target_language": target_language,
            "translated_text": translated_text,
            "download_url": f"/notes/{translation_id}/download",
        }
    ), 200


@app.route("/synthesize", methods=["POST"])
def synthesize():
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    target_language = data.get("target_language", "Spanish")

    if not text:
        return jsonify({"error": "Missing required field: 'text'"}), 400
    if target_language not in TARGET_LANGUAGES:
        return jsonify(
            {"error": f"Unsupported target language: {target_language}"}
        ), 400
    if len(text) > MAX_TTS_CHARS:
        return jsonify(
            {"error": f"Text exceeds {MAX_TTS_CHARS} character limit for TTS"}
        ), 413

    try:
        audio_bytes = _call_tts(text, target_language)
    except requests.HTTPError as e:
        return jsonify(
            {
                "error": f"TTS failed: HTTP {e.response.status_code}: {e.response.text[:300]}"
            }
        ), 502
    except requests.RequestException as e:
        return jsonify({"error": f"TTS network error: {str(e)[:200]}"}), 502

    if not audio_bytes:
        return jsonify({"error": "TTS returned empty audio"}), 502

    audio_id = f"audio-{uuid.uuid4().hex[:8]}"
    _store[audio_id] = {
        "id": audio_id,
        "audio": audio_bytes,
        "target_language": target_language,
        "voice": TTS_VOICE,
        "created_at": time.time(),
        "_ts": time.time(),
    }

    return jsonify(
        {
            "audio_id": audio_id,
            "target_language": target_language,
            "voice": TTS_VOICE,
            "audio_url": f"/audio/{audio_id}",
            "download_url": f"/audio/{audio_id}/download",
        }
    ), 200


@app.route("/audio/<audio_id>", methods=["GET"])
def serve_audio(audio_id):
    item = _store.get(audio_id)
    if not item or "audio" not in item:
        return jsonify({"error": "audio not found"}), 404
    return Response(item["audio"], mimetype=f"audio/{TTS_AUDIO_FORMAT}")


@app.route("/audio/<audio_id>/download", methods=["GET"])
def download_audio(audio_id):
    item = _store.get(audio_id)
    if not item or "audio" not in item:
        return jsonify({"error": "audio not found"}), 404
    lang = item.get("target_language", "translated")
    prefix = LANGUAGE_FILE_PREFIX.get(lang, lang.lower())
    filename = _safe_filename(f"{prefix}-audio-{_today_str()}.{TTS_AUDIO_FORMAT}")
    buf = io.BytesIO(item["audio"])
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype=f"audio/{TTS_AUDIO_FORMAT}",
    )


@app.route("/notes/<note_id>/download", methods=["GET"])
def download_note(note_id):
    item = _store.get(note_id)
    if not item:
        return jsonify({"error": "note not found"}), 404

    if "translated_text" in item:
        lang = item.get("target_language", "translated")
        prefix = LANGUAGE_FILE_PREFIX.get(lang, lang.lower())
        content = item["translated_text"]
        filename = _safe_filename(f"{prefix}-translation-{_today_str()}.txt")
    elif "transcript" in item:
        content = item["transcript"]
        filename = _safe_filename(f"original-transcript-{_today_str()}.txt")
    else:
        return jsonify({"error": "note has no downloadable content"}), 400

    buf = io.BytesIO(content.encode("utf-8"))
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype="text/plain",
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "uptime_s": int(time.time() - _started_at),
            "stt_model": STT_MODEL,
            "translation_model": TRANSLATION_MODEL,
            "tts_voice": TTS_VOICE,
            "target_languages": TARGET_LANGUAGES,
        }
    ), 200


# ─── Browser UI ─────────────────────────────────────────────────────────────

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Telnyx Speech Translator</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #000; --panel: #0d0d0d; --border: #1f1f1f; --border-2: #2a2a2a;
    --text: #fafafa; --muted: #8a8a8a; --muted-2: #5a5a5a;
    --green: #00E3AA; --green-dim: #00B894; --cream: #F5F0E8; --red: #ff5a5a;
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif;
    font-size: 17px; line-height: 1.55; margin: 0; min-height: 100vh;
    -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 880px; margin: 0 auto; padding: 56px 24px 96px; }
  .brand { display: flex; align-items: center; gap: 12px; margin-bottom: 48px; }
  .brand img { height: 32px; }
  .brand .tag { color: var(--muted); font-size: 14px; }
  .brand .tag::before { content: '\\00b7'; margin: 0 10px; }
  h1 { font-size: 36px; font-weight: 700; letter-spacing: -0.03em; margin: 0 0 16px; color: var(--cream); }
  .lede { font-size: 18px; color: var(--muted); margin: 0 0 40px; line-height: 1.5; }
  .lede strong { color: var(--text); font-weight: 500; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 28px; margin-bottom: 24px; }
  .label { font-size: 12px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--green); margin: 0 0 12px; }
  .row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  button { background: var(--green); color: #000; border: none; padding: 14px 24px; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; font-family: inherit; transition: all 0.15s ease; }
  button:hover:not(:disabled) { background: #1BFFC2; }
  button:active:not(:disabled) { transform: translateY(1px); }
  button:disabled { background: #2a2a2a; color: #5a5a5a; cursor: default; }
  button.recording { background: var(--red); color: #fff; }
  button.secondary { background: transparent; color: var(--green); border: 1px solid var(--border-2); }
  button.secondary:hover:not(:disabled) { border-color: var(--green-dim); background: rgba(0,227,170,0.05); }
  .timer { font-size: 22px; font-weight: 600; color: var(--muted); font-variant-numeric: tabular-nums; min-width: 70px; }
  select { background: var(--bg); color: var(--text); border: 1px solid var(--border-2); border-radius: 10px; padding: 10px 14px; font-size: 15px; font-family: inherit; cursor: pointer; outline: none; }
  select:focus { border-color: var(--green-dim); }
  .status { font-size: 15px; color: var(--muted); margin-top: 16px; display: flex; align-items: center; gap: 10px; }
  .status .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted-2); display: inline-block; }
  .status.working .dot { background: var(--green); animation: pulse 1s ease infinite; }
  .status.done .dot { background: var(--green); }
  .status.err .dot { background: var(--red); }
  @keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(0.85); } }
  .audio-preview { margin-top: 16px; }
  .audio-preview audio { width: 100%; }
  .split { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  .col h3 { font-size: 14px; font-weight: 600; color: var(--green); margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.08em; }
  textarea { width: 100%; box-sizing: border-box; background: var(--bg); color: var(--cream); border: 1px solid var(--border-2); border-radius: 10px; padding: 14px; font-size: 15px; font-family: inherit; line-height: 1.5; resize: vertical; min-height: 120px; outline: none; }
  textarea:focus { border-color: var(--green-dim); }
  .dl-btn { display: inline-block; margin-top: 10px; background: transparent; color: var(--green); border: 1px solid var(--border-2); padding: 8px 16px; border-radius: 8px; font-size: 14px; font-weight: 500; text-decoration: none; }
  .dl-btn:hover { border-color: var(--green-dim); background: rgba(0,227,170,0.05); }
  .tts-section { margin-top: 24px; padding-top: 24px; border-top: 1px solid var(--border); }
  .meta { font-size: 13px; color: var(--muted-2); margin: 4px 0 0; }
  .footer { margin-top: 48px; padding-top: 28px; border-top: 1px solid var(--border); }
  .footer a { color: var(--green); text-decoration: none; font-size: 15px; font-weight: 500; }
  @media (max-width: 640px) {
    .split { grid-template-columns: 1fr; }
    .wrap { padding: 32px 16px 64px; }
    h1 { font-size: 28px; }
  }
  .hidden { display: none; }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">
    <img src="/telnyx-logo.svg" alt="Telnyx">
    <span class="tag">Voice AI</span>
  </div>
  <h1>Telnyx Speech Translator</h1>
  <p class="lede">Record your voice, transcribe it, translate it, and hear it in another language. <strong>STT &rarr; AI Inference &rarr; TTS</strong> on one platform.</p>

  <div class="panel">
    <p class="label">Record or upload audio</p>
    <div class="row">
      <button id="recordBtn" onclick="toggleRecording()">Record</button>
      <span class="timer" id="timer">0:00</span>
      <label for="uploadBtn" class="dl-btn" style="cursor:pointer">Upload audio file</label>
      <input type="file" id="uploadBtn" accept=".webm,.mp3,.wav,.m4a,.ogg,.flac,audio/*" style="display:none" onchange="handleUpload(event)">
    </div>
    <div class="status" id="statusRecord"><span class="dot"></span><span class="msg">Click record to start, or upload an audio file</span></div>
    <div id="audioPreview" class="audio-preview hidden"></div>
  </div>

  <div id="transcribePanel" class="panel hidden">
    <p class="label">Translate to</p>
    <div class="row">
      <select id="targetLang">
        <option value="Spanish" selected>Spanish</option>
        <option value="English">English</option>
        <option value="French">French</option>
        <option value="German">German</option>
        <option value="Italian">Italian</option>
        <option value="Portuguese">Portuguese</option>
        <option value="Hindi">Hindi</option>
        <option value="Japanese">Japanese</option>
      </select>
      <button id="transcribeBtn" onclick="transcribeAndTranslate()">Transcribe &amp; Translate to Spanish</button>
    </div>
    <div class="status" id="statusMain"><span class="dot"></span><span class="msg"></span></div>
  </div>

  <div id="resultsPanel" class="panel hidden">
    <p class="meta" id="metaInfo"></p>
    <div class="split">
      <div class="col">
        <h3>Original transcript</h3>
        <textarea id="originalText" placeholder="Transcript will appear here..."></textarea>
        <a class="dl-btn" id="dlOriginal" href="#" download>Download original .txt &darr;</a>
      </div>
      <div class="col">
        <h3 id="translatedHeader">Spanish translation</h3>
        <textarea id="translatedText" placeholder="Translation will appear here..."></textarea>
        <a class="dl-btn" id="dlTranslation" href="#" download>Download translation .txt &darr;</a>
      </div>
    </div>
    <div class="tts-section">
      <p class="label">Translated speech</p>
      <div id="audioResult" class="audio-preview hidden"></div>
      <span class="meta" id="ttsMeta"></span>
      <div class="status" id="statusTts"><span class="dot"></span><span class="msg"></span></div>
    </div>
  </div>

  <div class="footer">
    <a href="https://github.com/team-telnyx/telnyx-code-examples/tree/main/voice-to-text-note-taker-python" target="_blank">View source &rarr;</a>
  </div>
</div>

<script>
let mediaRecorder = null, audioChunks = [], startTime = 0, timerInterval = null;
let currentBlob = null;
let isRecording = false;

async function toggleRecording() {
  const btn = document.getElementById('recordBtn');
  if (isRecording) {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      currentBlob = new Blob(audioChunks, {type: 'audio/webm'});
      showAudioPreview(currentBlob);
      stopTimer();
      isRecording = false;
      btn.textContent = 'Record';
      btn.className = '';
      setRecordStatus('done', 'Recording complete. Pick a language and click Transcribe.');
    };
    mediaRecorder.start();
    isRecording = true;
    btn.textContent = 'Stop';
    btn.className = 'recording';
    startTimer();
    setRecordStatus('working', 'Recording... click Stop when done');
    document.getElementById('transcribePanel').classList.add('hidden');
    document.getElementById('resultsPanel').classList.add('hidden');
  } catch (e) { setRecordStatus('err', 'Microphone access denied'); }
}

function handleUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  currentBlob = file;
  showAudioPreview(file);
  setRecordStatus('done', 'File uploaded: ' + file.name);
  isRecording = false;
  document.getElementById('recordBtn').textContent = 'Record';
  document.getElementById('recordBtn').className = '';
}

function showAudioPreview(blob) {
  const url = URL.createObjectURL(blob);
  document.getElementById('audioPreview').innerHTML = '<audio controls src="' + url + '"></audio>';
  document.getElementById('audioPreview').classList.remove('hidden');
  document.getElementById('transcribePanel').classList.remove('hidden');
  document.getElementById('transcribeBtn').disabled = false;
}

function startTimer() {
  startTime = Date.now();
  document.getElementById('timer').textContent = '0:00';
  timerInterval = setInterval(() => {
    const s = Math.floor((Date.now() - startTime) / 1000);
    document.getElementById('timer').textContent = Math.floor(s/60) + ':' + String(s%60).padStart(2,'0');
  }, 200);
}
function stopTimer() { clearInterval(timerInterval); }

function setRecordStatus(state, msg) {
  const s = document.getElementById('statusRecord');
  s.className = 'status ' + state;
  s.querySelector('.msg').textContent = msg;
}
function setMainStatus(state, msg) {
  const s = document.getElementById('statusMain');
  s.className = 'status ' + state;
  s.querySelector('.msg').textContent = msg;
}
function setTtsStatus(state, msg) {
  const s = document.getElementById('statusTts');
  s.className = 'status ' + state;
  s.querySelector('.msg').textContent = msg;
}

document.getElementById('targetLang').addEventListener('change', function() {
  const lang = this.value;
  document.getElementById('transcribeBtn').textContent = 'Transcribe & Translate to ' + lang;
  document.getElementById('translatedHeader').textContent = lang + ' translation';
});

async function transcribeAndTranslate() {
  if (!currentBlob) return;
  const btn = document.getElementById('transcribeBtn');
  const lang = document.getElementById('targetLang').value;
  btn.disabled = true;

  // Step 1: STT — show transcript immediately
  setMainStatus('working', 'Transcribing with Telnyx STT...');
  const formData = new FormData();
  formData.append('audio', currentBlob, 'note.webm');

  try {
    const r = await fetch('/transcribe', { method: 'POST', body: formData });
    const j = await r.json();
    if (!r.ok) { setMainStatus('err', 'STT Error: ' + (j.error || 'unknown')); btn.disabled = false; return; }

    document.getElementById('originalText').value = j.transcript;
    document.getElementById('metaInfo').textContent = 'Detected: ' + j.detected_language + ' | STT: ' + j.model + ' | ' + (j.duration_ms / 1000).toFixed(1) + 's';
    document.getElementById('dlOriginal').href = j.download_url;
    document.getElementById('resultsPanel').classList.remove('hidden');
    document.getElementById('translatedHeader').textContent = lang + ' translation';
    setMainStatus('done', 'Transcribed. Now translating to ' + lang + '...');

    // Step 2: Translate — show translation when Kimi finishes
    const r2 = await fetch('/translate', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ source_text: j.transcript, target_language: lang })
    });
    const j2 = await r2.json();
    if (!r2.ok) { setMainStatus('err', 'Translation Error: ' + (j2.error || 'unknown')); btn.disabled = false; return; }

    document.getElementById('translatedText').value = j2.translated_text;
    document.getElementById('dlTranslation').href = j2.download_url;
    setMainStatus('done', 'Translated to ' + lang + '. Generating audio...');

    // Step 3: TTS — show audio when ready
    setTtsStatus('working', 'Generating ' + lang + ' speech...');
    const r3 = await fetch('/synthesize', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ text: j2.translated_text, target_language: lang })
    });
    const j3 = await r3.json();
    if (!r3.ok) { setTtsStatus('err', 'TTS Error: ' + (j3.error || 'unknown')); setMainStatus('done', 'Translated to ' + lang + '.'); btn.disabled = false; return; }

    document.getElementById('audioResult').innerHTML = '<audio controls autoplay src="' + j3.audio_url + '"></audio><br><a class="dl-btn" href="' + j3.download_url + '" download>Download ' + lang + ' audio &darr;</a>';
    document.getElementById('audioResult').classList.remove('hidden');
    document.getElementById('ttsMeta').textContent = 'Voice: ' + j3.voice + ' | Language: ' + j3.target_language;
    setTtsStatus('done', lang + ' audio ready');
    setMainStatus('done', 'Done.');
  } catch (e) {
    setMainStatus('err', 'Network error');
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return INDEX_HTML


@app.route("/telnyx-logo.svg", methods=["GET"])
def logo():
    logo_path = os.path.join(os.path.dirname(__file__), "telnyx-logo.svg")
    try:
        with open(logo_path, "r", encoding="utf-8") as f:
            return Response(f.read(), mimetype="image/svg+xml")
    except FileNotFoundError:
        return Response("", status=404)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    host = os.getenv("HOST", "127.0.0.1")
    app.run(debug=False, port=port, host=host)
