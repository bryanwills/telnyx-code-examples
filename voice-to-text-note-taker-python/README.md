---
name: voice-to-text-note-taker
title: "Voice-to-Text Note Taker"
description: "Speak into a browser mic, Telnyx STT transcribes the recording, and you get a downloadable .txt file. No phone, no LLM, no streaming. The simplest possible STT demo."
language: python
framework: flask
telnyx_products: [Speech-to-Text]
channel: [api]
---

# Voice-to-Text Note Taker

Speak into a browser mic, click stop, and get a downloadable .txt file with your transcription. Telnyx Speech-to-Text handles the transcription via `POST /v2/ai/audio/transcriptions`. No phone, no LLM, no WebSocket streaming, no Cloud Storage. The simplest possible STT demo.

## Telnyx API Endpoints Used

- **Speech-to-Text (REST)**: `POST /v2/ai/audio/transcriptions` — [API reference](https://developers.telnyx.com/api/inference/transcribe)
  - Model: `openai/whisper-large-v3-turbo` (default, configurable via `STT_MODEL`)
  - Multipart file upload: `file` field with audio bytes
  - Form data: `model` field, optional `language` field
  - Returns JSON with `text` field containing the transcript

## Architecture

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

## How It Works

1. The browser captures audio via `navigator.mediaDevices.getUserMedia` and `MediaRecorder`.
2. When the user clicks Stop, the audio Blob is POSTed to `/transcribe` as a multipart file upload.
3. The Flask app forwards the file to Telnyx STT (`POST /v2/ai/audio/transcriptions`) with the model name.
4. Telnyx returns the transcript as JSON with a `text` field.
5. The app stores the transcript in memory and returns a `note_id` + `download_url`.
6. The user can download the transcript as a `.txt` file via `GET /notes/<note_id>/download`.

## Why Telnyx

Telnyx AI Communications Infrastructure exposes Speech-to-Text via a simple REST endpoint. No streaming WebSocket, no SDK, no phone number required. One multipart upload, one JSON response. This example shows the bare minimum — the simplest possible way to turn speech into text on Telnyx.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `STT_MODEL` | `string` | `openai/whisper-large-v3-turbo` | no | STT model (default: Whisper) | [Models](https://developers.telnyx.com/docs/inference/models) |

No phone number, connection ID, public key, or webhook URL is required.

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/voice-to-text-note-taker-python
cp .env.example .env    # ← fill in your TELNYX_API_KEY
pip install -r requirements.txt
python app.py           # starts on http://127.0.0.1:5050
```

Open `http://127.0.0.1:5050/` in your browser, click Record, speak, click Stop. The transcript appears and you can download it as a .txt file.

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/voice-to-text-note-taker-python/API.md) for the full typed endpoint reference. Quick start:

```bash
# Transcribe an audio file
curl -X POST http://localhost:5050/transcribe \
  -F audio=@note.webm

# Download the transcript
curl -OJ http://localhost:5050/notes/<note_id>/download
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Missing or invalid `TELNYX_API_KEY` | Set `TELNYX_API_KEY` in `.env` |
| `400` from STT | Audio format not recognized | Ensure the uploaded file has a recognized extension (.webm, .mp3, .wav, .m4a, .ogg, .flac) |
| `502` with "STT returned empty transcript" | Audio too short or silent | Record at least 1 second of speech |
| Browser mic not working | Permission denied or no mic | Check browser permissions for microphone access |
| Port 5000 already in use | macOS AirPlay Receiver holds port 5000 | App defaults to `PORT=5050` |

## Related Examples

- [`ai-content-translator-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-content-translator-python) — STT + AI translate + TTS pipeline (file upload)
- [`ai-voicemail-transcription-forwarding-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-voicemail-transcription-forwarding-python) — STT on phone voicemail audio
- [`voice-journal-daily-log-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/voice-journal-daily-log-python) — phone-based voice journal with AI mood extraction
- [`media-stream-live-transcription-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/media-stream-live-transcription-python) — live transcription of a phone call's media stream

## Agent Discovery

This example is part of the [Telnyx Code Examples](https://github.com/team-telnyx/telnyx-code-examples) catalog.

- **Agent signup**: [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md) — automated account provisioning via agent mail; get an API key with no human intervention
- **Agent CLI**: [github.com/team-telnyx/ai/tree/main/cli](https://github.com/team-telnyx/ai/tree/main/cli) — composite commands for agents ([commands reference](https://github.com/team-telnyx/ai/tree/main/cli/src/commands))
- **Agent skills**: [github.com/team-telnyx/ai/tree/main/skills](https://github.com/team-telnyx/ai/tree/main/skills)
- **Telnyx AI repo**: [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLM-optimized docs**: [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt)
- **Example index**: [`llms.txt`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/llms.txt)
- **Telnyx CLI (human)**: [developers.telnyx.com/development/cli](https://developers.telnyx.com/development/cli) — `go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest`

## Resources

- STT API reference: [developers.telnyx.com/api/inference/transcribe](https://developers.telnyx.com/api/inference/transcribe)
- STT overview: [developers.telnyx.com/docs/ai-stt](https://developers.telnyx.com/docs/ai-stt)
- Available models: [developers.telnyx.com/docs/inference/models](https://developers.telnyx.com/docs/inference/models)
- Repo CONTRIBUTING.md: [github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md](https://github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md)
