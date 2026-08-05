#!/usr/bin/env python3
"""Voice Flashcards — TTS speaks a phrase in Spanish, you repeat it, STT
transcribes your speech, and Inference scores your pronunciation. Interactive
language learning powered by all three Telnyx AI primitives on one platform.

No phone, no database, no Cloud Storage. Three REST calls:
  1. POST /v2/text-to-speech/speech          (TTS plays the flashcard)
  2. POST /v2/ai/audio/transcriptions         (STT transcribes your speech)
  3. POST /v2/ai/chat/completions             (Inference scores your answer)

The browser never receives the API key.
"""

import io
import os
import json
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
INFERENCE_MODEL = os.getenv("TRANSLATION_MODEL", "moonshotai/Kimi-K2.6")

TTS_ENDPOINT = "https://api.telnyx.com/v2/text-to-speech/speech"
TTS_VOICE = os.getenv("TTS_VOICE", "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f")
TTS_AUDIO_FORMAT = os.getenv("TTS_AUDIO_FORMAT", "mp3")

MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024
MAX_CHECK_CHARS = 1000
TEMP_FILE_TTL_SECONDS = int(os.getenv("TEMP_FILE_TTL_MINUTES", "30")) * 60

SUPPORTED_AUDIO_EXTS = {".webm", ".mp3", ".wav", ".m4a", ".ogg", ".flac"}

LANGUAGE_BOOST_MAP = {
    "Spanish": "Spanish",
    "French": "French",
    "German": "German",
    "Italian": "Italian",
    "Portuguese": "Portuguese",
    "Japanese": "Japanese",
    "Hindi": "Hindi",
    "English": "English",
}

FLASHCARD_DECKS = {
    "Spanish — Greetings": {
        "language": "Spanish",
        "cards": [
            {"phrase": "Hola, como estas?", "translation": "Hello, how are you?"},
            {"phrase": "Buenos dias", "translation": "Good morning"},
            {"phrase": "Buenas tardes", "translation": "Good afternoon"},
            {"phrase": "Mucho gusto en conocerte", "translation": "Nice to meet you"},
            {"phrase": "Hasta luego", "translation": "See you later"},
            {"phrase": "Como te llamas?", "translation": "What is your name?"},
            {"phrase": "Me llamo Ana", "translation": "My name is Ana"},
            {"phrase": "De donde eres?", "translation": "Where are you from?"},
        ],
    },
    "Spanish — Numbers": {
        "language": "Spanish",
        "cards": [
            {"phrase": "Uno, dos, tres", "translation": "One, two, three"},
            {"phrase": "Cinco", "translation": "Five"},
            {"phrase": "Diez", "translation": "Ten"},
            {"phrase": "Veinte", "translation": "Twenty"},
            {"phrase": "Cien", "translation": "One hundred"},
            {"phrase": "Mil", "translation": "One thousand"},
        ],
    },
    "Spanish — Common phrases": {
        "language": "Spanish",
        "cards": [
            {"phrase": "Por favor", "translation": "Please"},
            {"phrase": "Gracias", "translation": "Thank you"},
            {"phrase": "De nada", "translation": "You're welcome"},
            {"phrase": "Lo siento", "translation": "I'm sorry"},
            {"phrase": "No entiendo", "translation": "I don't understand"},
            {"phrase": "Puedes repetir?", "translation": "Can you repeat?"},
            {"phrase": "Donde esta el bano?", "translation": "Where is the bathroom?"},
            {"phrase": "Cuanto cuesta?", "translation": "How much does it cost?"},
        ],
    },
    "French — Greetings": {
        "language": "French",
        "cards": [
            {
                "phrase": "Bonjour, comment allez-vous?",
                "translation": "Hello, how are you?",
            },
            {"phrase": "Bonsoir", "translation": "Good evening"},
            {"phrase": "Enchante", "translation": "Nice to meet you"},
            {"phrase": "Au revoir", "translation": "Goodbye"},
            {
                "phrase": "Comment vous appelez-vous?",
                "translation": "What is your name?",
            },
            {"phrase": "Je m'appelle Marie", "translation": "My name is Marie"},
        ],
    },
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


def _call_tts(text, language):
    voice_settings = {}
    boost = LANGUAGE_BOOST_MAP.get(language)
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


def _call_stt(audio_bytes, filename="audio.webm"):
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


def _call_check(target_phrase, spoken_text, language):
    system_prompt = (
        "You are a language pronunciation checker. "
        "Compare the target phrase with what the user said. "
        "Return ONLY valid JSON with no markdown:\n"
        '{"score": "correct"|"close"|"wrong", "feedback": "one short sentence tip"}\n\n'
        "Rules:\n"
        "- correct: the spoken text matches the target phrase (minor accent/Article differences are OK)\n"
        "- close: mostly right but has a noticeable error (wrong word, missing word, or strong accent)\n"
        "- wrong: does not match or unintelligible\n"
        "- feedback: one short sentence, in English, with a tip or encouragement\n"
        "- Do not include any text outside the JSON object"
    )
    user_content = (
        f"Target phrase ({language}): {target_phrase}\nUser said: {spoken_text}"
    )
    body = {
        "model": INFERENCE_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
        "max_tokens": 200,
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
        raise ValueError("Inference returned empty content")
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"Inference returned invalid JSON: {content[:200]}")
    if "score" not in result:
        raise ValueError("Inference response missing 'score' field")
    result["score"] = result["score"].lower().strip()
    if result["score"] not in ("correct", "close", "wrong"):
        result["score"] = "wrong"
    if "feedback" not in result or not result["feedback"]:
        result["feedback"] = ""
    return result


@app.route("/decks", methods=["GET"])
def decks():
    return jsonify({"decks": list(FLASHCARD_DECKS.keys())})


@app.route("/deck/<path:deck_name>", methods=["GET"])
def deck(deck_name):
    deck = FLASHCARD_DECKS.get(deck_name)
    if not deck:
        return jsonify({"error": "deck not found"}), 404
    return jsonify(
        {
            "name": deck_name,
            "language": deck["language"],
            "cards": deck["cards"],
        }
    )


@app.route("/speak", methods=["POST"])
def speak():
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    language = data.get("language", "Spanish")

    if not text:
        return jsonify({"error": "Missing required field: 'text'"}), 400
    if language not in LANGUAGE_BOOST_MAP:
        return jsonify({"error": f"Unsupported language: {language}"}), 400

    try:
        audio_bytes = _call_tts(text, language)
    except requests.HTTPError:
        return jsonify({"error": "TTS failed"}), 502
    except requests.RequestException:
        return jsonify({"error": "TTS network error"}), 502

    if not audio_bytes:
        return jsonify({"error": "TTS returned empty audio"}), 502

    audio_id = f"audio-{uuid.uuid4().hex[:8]}"
    _store[audio_id] = {
        "id": audio_id,
        "audio": audio_bytes,
        "language": language,
        "voice": TTS_VOICE,
        "created_at": time.time(),
        "_ts": time.time(),
    }

    return jsonify(
        {
            "audio_id": audio_id,
            "audio_url": f"/audio/{audio_id}",
        }
    ), 200


@app.route("/audio/<audio_id>", methods=["GET"])
def serve_audio(audio_id):
    item = _store.get(audio_id)
    if not item or "audio" not in item:
        return jsonify({"error": "audio not found"}), 404
    return Response(item["audio"], mimetype=f"audio/{TTS_AUDIO_FORMAT}")


@app.route("/check", methods=["POST"])
def check():
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    if "audio" not in request.files:
        return jsonify({"error": "Missing required file upload: 'audio'"}), 400

    target_phrase = request.form.get("target_phrase", "").strip()
    language = request.form.get("language", "Spanish")
    if not target_phrase:
        return jsonify({"error": "Missing required field: 'target_phrase'"}), 400
    if len(target_phrase) > MAX_CHECK_CHARS:
        return jsonify({"error": "Target phrase too long"}), 413

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
        return jsonify({"error": f"Unsupported file format: {ext}"}), 400

    try:
        stt_result = _call_stt(audio_bytes, filename)
    except requests.HTTPError:
        return jsonify({"error": "STT failed"}), 502
    except requests.RequestException:
        return jsonify({"error": "STT network error"}), 502

    spoken_text = stt_result.get("text", "").strip()
    if not spoken_text:
        return jsonify({"error": "STT returned empty transcript"}), 502

    try:
        result = _call_check(target_phrase, spoken_text, language)
    except requests.HTTPError:
        return jsonify({"error": "Inference failed"}), 502
    except requests.RequestException:
        return jsonify({"error": "Inference network error"}), 502
    except ValueError:
        return jsonify({"error": "Inference returned invalid response"}), 502

    return jsonify(
        {
            "target_phrase": target_phrase,
            "spoken_text": spoken_text,
            "language": language,
            "score": result["score"],
            "feedback": result["feedback"],
        }
    ), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "uptime_s": int(time.time() - _started_at),
            "stt_model": STT_MODEL,
            "inference_model": INFERENCE_MODEL,
            "tts_voice": TTS_VOICE,
            "decks": list(FLASHCARD_DECKS.keys()),
        }
    ), 200


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Flashcards — Telnyx</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #000; --panel: #0d0d0d; --border: #1f1f1f; --border-2: #2a2a2a;
    --text: #fafafa; --muted: #8a8a8a; --muted-2: #5a5a5a;
    --green: #00E3AA; --green-dim: #00B894; --cream: #F5F0E8;
    --red: #ff5a5a; --yellow: #ffc83d;
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif;
    font-size: 17px; line-height: 1.55; margin: 0; min-height: 100vh;
    -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 640px; margin: 0 auto; padding: 56px 24px 96px; }
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
  .card-phrase { font-size: 28px; font-weight: 600; color: var(--cream); margin: 16px 0 8px; text-align: center; }
  .card-translation { font-size: 16px; color: var(--muted); text-align: center; margin: 0 0 20px; }
  .card-audio { margin: 16px 0; }
  .card-audio audio { width: 100%; }
  .score-badge { display: inline-block; padding: 6px 16px; border-radius: 8px; font-size: 18px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
  .score-correct { background: rgba(0,227,170,0.15); color: var(--green); }
  .score-close { background: rgba(255,200,61,0.15); color: var(--yellow); }
  .score-wrong { background: rgba(255,90,90,0.15); color: var(--red); }
  .compare { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 16px 0; }
  .compare h4 { font-size: 13px; font-weight: 600; color: var(--green); margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.08em; }
  .compare p { margin: 0; color: var(--cream); font-size: 16px; line-height: 1.4; }
  .feedback { font-size: 16px; color: var(--muted); margin: 12px 0 0; font-style: italic; }
  .progress { font-size: 14px; color: var(--muted-2); margin: 0 0 20px; }
  .footer { margin-top: 48px; padding-top: 28px; border-top: 1px solid var(--border); }
  .footer a { color: var(--green); text-decoration: none; font-size: 15px; font-weight: 500; }
  @media (max-width: 640px) {
    .compare { grid-template-columns: 1fr; }
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
  <h1>Voice Flashcards</h1>
  <p class="lede">Listen to a phrase, repeat it back, and get instant pronunciation feedback. <strong>TTS speaks, you repeat, STT transcribes, Inference scores</strong> — all on Telnyx.</p>

  <div class="panel">
    <p class="label">Choose a deck</p>
    <select id="deckSelect" onchange="loadDeck()"></select>
  </div>

  <div id="cardPanel" class="panel hidden">
    <p class="progress" id="progress">Card 1 of 0</p>
    <p class="label">Listen and repeat</p>
    <div class="card-phrase" id="cardPhrase"></div>
    <div class="card-translation" id="cardTranslation"></div>
    <div class="card-audio" id="cardAudio"></div>
    <div class="row">
      <button id="recordBtn" onclick="toggleRecording()">Record</button>
      <span class="timer" id="timer">0:00</span>
      <button class="secondary" id="skipBtn" onclick="nextCard()">Skip</button>
    </div>
    <div class="status" id="status"><span class="dot"></span><span class="msg">Click record, then repeat the phrase</span></div>
  </div>

  <div id="resultPanel" class="panel hidden">
    <div class="row" style="justify-content: center;">
      <span class="score-badge" id="scoreBadge"></span>
    </div>
    <div class="compare">
      <div>
        <h4>Target</h4>
        <p id="targetText"></p>
      </div>
      <div>
        <h4>You said</h4>
        <p id="spokenText"></p>
      </div>
    </div>
    <p class="feedback" id="feedbackText"></p>
    <div class="row" style="margin-top: 20px;">
      <button onclick="nextCard()">Next card</button>
      <button class="secondary" onclick="retryCard()">Try again</button>
    </div>
  </div>

  <div class="footer">
    <a href="https://github.com/team-telnyx/telnyx-code-examples/tree/main/voice-to-text-note-taker-python" target="_blank">View source &rarr;</a>
  </div>
</div>

<script>
let currentDeck = null;
let cardIndex = 0;
let mediaRecorder = null, audioChunks = [], startTime = 0, timerInterval = null;
let isRecording = false;

async function init() {
  const r = await fetch('/decks');
  const j = await r.json();
  const select = document.getElementById('deckSelect');
  j.decks.forEach(name => {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
  });
  if (j.decks.length > 0) loadDeck();
}

async function loadDeck() {
  const name = document.getElementById('deckSelect').value;
  const r = await fetch('/deck/' + encodeURIComponent(name));
  const j = await r.json();
  currentDeck = j;
  cardIndex = 0;
  showCard();
}

async function showCard() {
  if (!currentDeck || cardIndex >= currentDeck.cards.length) {
    document.getElementById('cardPanel').classList.add('hidden');
    document.getElementById('resultPanel').classList.add('hidden');
    setStatus('done', 'Deck complete.');
    return;
  }
  const card = currentDeck.cards[cardIndex];
  document.getElementById('progress').textContent = 'Card ' + (cardIndex + 1) + ' of ' + currentDeck.cards.length;
  document.getElementById('cardPhrase').textContent = card.phrase;
  document.getElementById('cardTranslation').textContent = card.translation;
  document.getElementById('cardAudio').innerHTML = '';
  document.getElementById('resultPanel').classList.add('hidden');
  document.getElementById('cardPanel').classList.remove('hidden');
  setStatus('', 'Click record, then repeat the phrase');

  const r = await fetch('/speak', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ text: card.phrase, language: currentDeck.language })
  });
  const j = await r.json();
  if (j.audio_url) {
    document.getElementById('cardAudio').innerHTML = '<audio controls autoplay src="' + j.audio_url + '"></audio>';
  }
}

function nextCard() {
  cardIndex++;
  showCard();
}

function retryCard() {
  document.getElementById('resultPanel').classList.add('hidden');
  document.getElementById('cardPanel').classList.remove('hidden');
  setStatus('', 'Click record, then repeat the phrase');
}

async function toggleRecording() {
  const btn = document.getElementById('recordBtn');
  if (isRecording) {
    if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(audioChunks, {type: 'audio/webm'});
      stopTimer();
      isRecording = false;
      btn.textContent = 'Record';
      btn.className = '';
      checkAnswer(blob);
    };
    mediaRecorder.start();
    isRecording = true;
    btn.textContent = 'Stop';
    btn.className = 'recording';
    startTimer();
    setStatus('working', 'Recording... click Stop when done');
  } catch (e) { setStatus('err', 'Microphone access denied'); }
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

function setStatus(state, msg) {
  const s = document.getElementById('status');
  s.className = 'status ' + state;
  s.querySelector('.msg').textContent = msg;
}

async function checkAnswer(blob) {
  if (!currentDeck || cardIndex >= currentDeck.cards.length) return;
  const card = currentDeck.cards[cardIndex];
  setStatus('working', 'Checking your pronunciation...');

  const formData = new FormData();
  formData.append('audio', blob, 'answer.webm');
  formData.append('target_phrase', card.phrase);
  formData.append('language', currentDeck.language);

  try {
    const r = await fetch('/check', { method: 'POST', body: formData });
    const j = await r.json();
    if (!r.ok) { setStatus('err', 'Error: ' + (j.error || 'unknown')); return; }

    document.getElementById('cardPanel').classList.add('hidden');
    document.getElementById('scoreBadge').textContent = j.score;
    document.getElementById('scoreBadge').className = 'score-badge score-' + j.score;
    document.getElementById('targetText').textContent = j.target_phrase;
    document.getElementById('spokenText').textContent = j.spoken_text;
    document.getElementById('feedbackText').textContent = j.feedback || '';
    document.getElementById('resultPanel').classList.remove('hidden');
    setStatus('done', j.score === 'correct' ? 'Correct.' : j.score === 'close' ? 'Close.' : 'Try again.');
  } catch (e) {
    setStatus('err', 'Network error');
  }
}

init();
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
