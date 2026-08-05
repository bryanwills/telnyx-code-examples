# Build a Voice-to-Text Note Taker with Telnyx STT

Speak into a browser mic, click stop, and get a downloadable .txt file with your transcription. The simplest possible STT demo — no phone, no LLM, no streaming.

## How It Works

```
  Browser (mic)
        │  (MediaRecorder → Blob)
        ▼
  POST /transcribe  (multipart file upload)
        │
        ▼
  ┌──────────────────────┐
  │ Telnyx STT REST      │  POST /v2/ai/audio/transcriptions
  │ (Whisper)            │  model=openai/whisper-large-v3-turbo
  └────────┬─────────────┘
           │
           ▼
  Save transcript as .txt in memory
           │
           ▼
  Return: note_id, transcript, download_url
  GET /notes/<id>/download → .txt file
```

## Telnyx Products Used

- **Speech-to-Text** — REST endpoint at `POST /v2/ai/audio/transcriptions` with multipart file upload. Returns JSON with a `text` field containing the transcript. No streaming, no WebSocket, no SDK required.

## API Endpoints

- **Speech-to-Text**: `POST /v2/ai/audio/transcriptions` — [API reference](https://developers.telnyx.com/api/inference/transcribe)
  - Multipart form: `file` (audio bytes), `model` (e.g. `openai/whisper-large-v3-turbo`)
  - Optional: `language` field for source language hint
  - Response: JSON with `text` field

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- A Telnyx API v2 key from the [Portal](https://portal.telnyx.com/api-keys)
- A browser with microphone access (Chrome, Firefox, Safari, Edge)

No phone number, TeXML application, or webhook endpoint is required.

## Step 1 — Configure environment

```bash
cp .env.example .env
# Edit .env and set TELNYX_API_KEY
```

## Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

## Step 3 — Run the app

```bash
python app.py
# * Running on http://127.0.0.1:5050
```

The app defaults to port 5050 to avoid conflicts with macOS AirPlay Receiver on port 5000. Override with `PORT=xxxx python app.py`.

## Step 4 — Record a note

1. Open `http://127.0.0.1:5050/` in your browser.
2. Click **Record** — the browser asks for microphone permission.
3. Speak your note.
4. Click **Stop** — the audio is sent to Telnyx STT for transcription.
5. The transcript appears on screen.
6. Click **Download .txt** to save the transcript as a text file.

## Step 5 — Transcribe via curl

You can also transcribe any audio file without the browser UI:

```bash
# Transcribe an audio file
curl -X POST http://localhost:5050/transcribe \
  -F audio=@my-note.mp3

# Response:
# {"note_id": "note-a1b2c3d4", "transcript": "...", "download_url": "/notes/note-a1b2c3d4/download"}

# Download the transcript
curl -OJ http://localhost:5050/notes/note-a1b2c3d4/download
```

## How the browser audio capture works

The browser UI uses the standard Web Audio API:

1. `navigator.mediaDevices.getUserMedia({audio: true})` — request mic access
2. `MediaRecorder` — record audio as the user speaks
3. On stop, the recorded chunks are combined into a `Blob` with `type: 'audio/webm'`
4. The Blob is POSTed to `/transcribe` as a multipart form upload
5. Flask forwards it to Telnyx STT and returns the transcript

No audio processing happens in the browser — the raw WebM/Opus recording is sent directly to Telnyx. Whisper handles the format natively.

## Notes and caveats

- **One env var.** Only `TELNYX_API_KEY` is required. No phone, no connection, no webhook.
- **In-memory store with 1-hour TTL.** Transcripts are held in process memory and expire after one hour. Use a database or Cloud Storage for production.
- **Whisper model.** The default model is `openai/whisper-large-v3-turbo`. Override via `STT_MODEL` env var if you want to use a different model.
- **Audio formats.** The browser records in WebM/Opus. Whisper also accepts mp3, wav, m4a, ogg, and flac when uploading via curl.
- **No streaming.** This is a batch transcribe — the full audio is uploaded, then the full transcript is returned. For real-time captions, see the Caption Studio example (planned).

## Next steps

- Add a `language` field to the form data for non-English audio.
- Add a `response_format` field to get JSON with word-level timestamps.
- Add Cloud Storage to persist transcripts as files with shareable URLs.
- Add a UI to list and re-download past notes.
