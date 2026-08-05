#!/usr/bin/env python3
"""Voice-to-Text Note Taker — speak into a browser mic, Telnyx STT transcribes
the recording, and you get a downloadable .txt file. No phone, no LLM, no
streaming. The simplest possible STT demo."""

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
STT_ENDPOINT = "https://api.telnyx.com/v2/ai/audio/transcriptions"
STT_MODEL = os.getenv("STT_MODEL", "openai/whisper-large-v3-turbo")

notes = {}
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


_start_ttl_cleanup(notes)


def transcribe(audio_bytes, filename="audio.webm"):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".webm", ".mp3", ".wav", ".m4a", ".ogg", ".flac"):
        ext = ".webm"
        filename = f"audio{ext}"
    files = {"file": (filename, audio_bytes, "application/octet-stream")}
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


@app.route("/transcribe", methods=["POST"])
def transcribe_endpoint():
    if not TELNYX_API_KEY:
        return jsonify({"error": "TELNYX_API_KEY is not set"}), 500

    if "audio" not in request.files:
        return jsonify({"error": "Missing required file upload: 'audio'"}), 400

    audio_file = request.files["audio"]
    audio_bytes = audio_file.read()
    if not audio_bytes:
        return jsonify({"error": "Audio file is empty"}), 400

    filename = audio_file.filename or "audio.webm"

    try:
        result = transcribe(audio_bytes, filename)
    except requests.HTTPError as e:
        return jsonify(
            {
                "error": f"STT failed: HTTP {e.response.status_code}: {e.response.text[:300]}"
            }
        ), 502
    except requests.RequestException as e:
        return jsonify({"error": f"network: {str(e)[:200]}"}), 502

    transcript = result.get("text", "")
    if not transcript:
        return jsonify({"error": "STT returned empty transcript"}), 502

    note_id = f"note-{uuid.uuid4().hex[:8]}"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    txt_content = f"Voice Note — {timestamp}\n\n{transcript}\n"

    notes[note_id] = {
        "id": note_id,
        "transcript": transcript,
        "txt_content": txt_content,
        "created_at": time.time(),
        "_ts": time.time(),
    }

    return jsonify(
        {
            "note_id": note_id,
            "transcript": transcript,
            "timestamp": timestamp,
            "download_url": f"/notes/{note_id}/download",
        }
    ), 200


@app.route("/notes/<note_id>/download", methods=["GET"])
def download_note(note_id):
    note = notes.get(note_id)
    if not note:
        return jsonify({"error": "note not found"}), 404

    import io

    buf = io.BytesIO(note["txt_content"].encode("utf-8"))
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"{note_id}.txt",
        mimetype="text/plain",
    )


@app.route("/notes", methods=["GET"])
def list_notes():
    return jsonify(
        {
            "notes": [
                {
                    "id": n["id"],
                    "transcript": n["transcript"][:200],
                    "created_at": n["created_at"],
                }
                for n in sorted(
                    notes.values(), key=lambda x: x["created_at"], reverse=True
                )
            ]
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "uptime_s": int(time.time() - _started_at)}), 200


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice-to-Text Note Taker — Telnyx</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #000; --panel: #0d0d0d; --border: #1f1f1f; --border-2: #2a2a2a;
    --text: #fafafa; --muted: #8a8a8a; --muted-2: #5a5a5a;
    --green: #00E3AA; --green-dim: #00B894; --cream: #F5F0E8;
    --red: #ff5a5a;
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
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 28px; }
  .label { font-size: 12px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--green); margin: 0 0 12px; }
  .record-row { display: flex; align-items: center; gap: 16px; }
  button { background: var(--green); color: #000; border: none; padding: 16px 28px; border-radius: 12px; font-size: 17px; font-weight: 600; cursor: pointer; font-family: inherit; transition: all 0.15s ease; }
  button:hover { background: #1BFFC2; }
  button:active { transform: translateY(1px); }
  button:disabled { background: #2a2a2a; color: #5a5a5a; cursor: default; }
  button.recording { background: var(--red); color: #fff; }
  .timer { font-size: 24px; font-weight: 600; color: var(--muted); font-variant-numeric: tabular-nums; min-width: 80px; }
  .status { font-size: 15px; color: var(--muted); margin-top: 20px; display: flex; align-items: center; gap: 10px; }
  .status .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted-2); display: inline-block; }
  .status.working .dot { background: var(--green); animation: pulse 1s ease infinite; }
  .status.done .dot { background: var(--green); }
  .status.err .dot { background: var(--red); }
  @keyframes pulse { 0%,100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } }
  #result { margin-top: 32px; }
  .result-card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 28px; animation: rise 0.3s ease; }
  @keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  .transcript { font-size: 17px; color: var(--cream); line-height: 1.6; white-space: pre-wrap; margin: 16px 0 0; }
  .timestamp { font-size: 13px; color: var(--muted-2); margin: 0 0 8px; }
  .download-btn { display: inline-block; margin-top: 16px; background: transparent; color: var(--green); border: 1px solid var(--border-2); padding: 10px 20px; border-radius: 10px; font-size: 15px; font-weight: 500; text-decoration: none; }
  .download-btn:hover { border-color: var(--green-dim); background: rgba(0,227,170,0.05); }
  .footer { margin-top: 48px; padding-top: 28px; border-top: 1px solid var(--border); }
  .footer a { color: var(--green); text-decoration: none; font-size: 15px; font-weight: 500; }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand">
    <img src="/telnyx-logo.svg" alt="Telnyx">
    <span class="tag">Voice AI</span>
  </div>
  <h1>Voice-to-Text Note Taker</h1>
  <p class="lede">
    Click record, speak, click stop. Telnyx <strong>Speech-to-Text</strong> transcribes your recording
    and gives you a downloadable .txt file. No phone, no LLM, just STT.
  </p>

  <div class="panel">
    <p class="label">Record your note</p>
    <div class="record-row">
      <button id="recordBtn" onclick="toggleRecording()">Record</button>
      <span class="timer" id="timer">0:00</span>
    </div>
    <div class="status" id="status"><span class="dot"></span><span class="msg">Click record to start</span></div>
  </div>

  <div id="result"></div>

  <div class="footer">
    <a href="https://github.com/team-telnyx/telnyx-code-examples/tree/main/voice-to-text-note-taker-python" target="_blank">View source &rarr;</a>
  </div>
</div>

<script>
let mediaRecorder = null;
let audioChunks = [];
let startTime = 0;
let timerInterval = null;

async function toggleRecording() {
  const btn = document.getElementById('recordBtn');
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(audioChunks, {type: 'audio/webm'});
      await transcribe(blob);
    };
    mediaRecorder.start();
    btn.textContent = 'Stop';
    btn.className = 'recording';
    startTimer();
    setStatus('working', 'Recording... click stop when done');
  } catch (e) {
    setStatus('err', 'Microphone access denied or unavailable');
  }
}

function startTimer() {
  startTime = Date.now();
  document.getElementById('timer').textContent = '0:00';
  timerInterval = setInterval(() => {
    const s = Math.floor((Date.now() - startTime) / 1000);
    document.getElementById('timer').textContent = `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
  }, 200);
}

function stopTimer() {
  clearInterval(timerInterval);
}

function setStatus(state, msg) {
  const s = document.getElementById('status');
  s.className = 'status ' + state;
  s.querySelector('.msg').textContent = msg;
}

async function transcribe(blob) {
  const btn = document.getElementById('recordBtn');
  btn.disabled = true;
  btn.textContent = 'Stop';
  stopTimer();
  setStatus('working', 'Transcribing...');

  const formData = new FormData();
  formData.append('audio', blob, 'note.webm');

  try {
    const r = await fetch('/transcribe', { method: 'POST', body: formData });
    const j = await r.json();
    if (!r.ok) { setStatus('err', 'Error: ' + (j.error || 'unknown')); return; }
    setStatus('done', 'Note transcribed');
    showResult(j);
  } catch (e) {
    setStatus('err', 'Network error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Record';
    btn.className = '';
  }
}

function showResult(j) {
  document.getElementById('result').innerHTML = `
    <div class="result-card">
      <p class="label">Your note</p>
      <p class="timestamp">${j.timestamp}</p>
      <div class="transcript">${escapeHtml(j.transcript)}</div>
      <a class="download-btn" href="${j.download_url}" download>Download .txt &darr;</a>
    </div>
  `;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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
