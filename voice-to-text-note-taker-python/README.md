---
name: voice-to-text-note-taker
title: "Telnyx Speech Translator"
description: "Record your voice, transcribe it, translate it, and hear it in another language. STT → AI Inference → TTS on one platform. No phone, no database, no Cloud Storage."
language: python
framework: flask
telnyx_products: [Speech-to-Text, AI Inference, Text-to-Speech]
channel: [api]
---

# Telnyx Speech Translator

Record your voice, transcribe it, translate it, and hear it in another language. The default flow: speak in English → Telnyx STT transcribes → Telnyx Inference translates to Spanish → Telnyx TTS generates Spanish audio → you listen and download.

No phone, no database, no Cloud Storage, no AI Assistant. Three REST calls on one platform.

## Architecture

```
Browser microphone or audio upload
              ↓
       POST /transcribe
              ↓
 Telnyx Speech-to-Text REST API
              ↓
      Editable transcript
              ↓
        POST /translate
              ↓
     Telnyx Inference API
              ↓
      Editable translation
              ↓
        POST /synthesize
              ↓
 Telnyx Text-to-Speech API
              ↓
   Audio playback and download
```

## Telnyx API Endpoints Used

- **Speech-to-Text (REST)**: `POST /v2/ai/audio/transcriptions` — [API reference](https://developers.telnyx.com/api/inference/transcribe)
  - Multipart file upload with `model` field
  - Model: `openai/whisper-large-v3-turbo` (default, configurable via `STT_MODEL`)
  - Returns JSON with `text` (transcript) and `language` (detected)
- **AI Inference (OpenAI-compatible)**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)
  - Model: `moonshotai/Kimi-K2.6` (default, configurable via `TRANSLATION_MODEL`)
  - System prompt: professional translator, preserve meaning/names/numbers, return only translation
  - Low temperature (0.1) for consistent translations
- **Text-to-Speech (REST)**: `POST /v2/text-to-speech/speech` — [API reference](https://developers.telnyx.com/api/inference/generate-speech-from-text)
  - Voice: Ultra voice UUID (default: Clara, configurable via `TTS_VOICE`)
  - `voice_settings.language_boost` for target language pronunciation
  - `output_type: binary_output` for audio bytes

> **The browser never receives the Telnyx API key.** All API calls are server-side.

## How It Works

1. **Record or upload** — the browser captures audio via `MediaRecorder` (WebM/Opus) or accepts a file upload (.webm, .mp3, .wav, .m4a, .ogg, .flac).
2. **Transcribe** — the audio is POSTed to `/transcribe`, which forwards it to Telnyx STT. The transcript appears in an editable text area.
3. **Translate** — the user picks a target language (Spanish, English, French, German, Italian, Portuguese, Hindi, Japanese) and clicks Translate. The backend calls Telnyx Inference with a strict translation prompt. The translation appears in an editable text area.
4. **Synthesize** — the user clicks Generate Audio. The backend calls Telnyx TTS with the translated text, the selected voice, and `language_boost` for the target language. An audio player appears with a download button.
5. **Download** — the user can download the original transcript (.txt), translated transcript (.txt), and generated audio (.mp3).

## Why Telnyx

Telnyx AI Communications Infrastructure exposes STT, AI Inference, and TTS as REST endpoints on one private backbone. This example chains all three in a single Flask app — no stitching separate vendors, no external API keys, no phone number. The browser captures audio, the server does the rest.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description |
|----------|------|---------|----------|-------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key |
| `STT_MODEL` | `string` | `openai/whisper-large-v3-turbo` | no | STT model (default: Whisper) |
| `TRANSLATION_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | Inference model for translation |
| `TTS_VOICE` | `string` | `Telnyx.Ultra.01eaafa9-...` | no | TTS voice UUID (default: Clara) |
| `TTS_AUDIO_FORMAT` | `string` | `mp3` | no | Audio format (default: mp3) |
| `MAX_AUDIO_SIZE_MB` | `int` | `25` | no | Max upload size (default: 25 MB) |
| `TEMP_FILE_TTL_MINUTES` | `int` | `30` | no | In-memory TTL (default: 30 min) |
| `PORT` | `int` | `5050` | no | Flask port (default: 5050) |
| `HOST` | `string` | `127.0.0.1` | no | Flask host |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/voice-to-text-note-taker-python
cp .env.example .env    # ← fill in your TELNYX_API_KEY
pip install -r requirements.txt
python app.py           # starts on http://127.0.0.1:5050
```

Open `http://127.0.0.1:5050/` in your browser. Record speech or upload an audio file, click Transcribe, pick a target language, click Translate, then click Generate Audio.

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/voice-to-text-note-taker-python/API.md) for the full typed endpoint reference. Quick start:

```bash
# Transcribe audio
curl -X POST http://localhost:5050/transcribe -F audio=@note.webm

# Translate transcript
curl -X POST http://localhost:5050/translate \
  -H "Content-Type: application/json" \
  -d '{"source_text":"Hello world","target_language":"Spanish"}'

# Generate translated speech
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola mundo","target_language":"Spanish"}'
```

## TTS Voice Selection

The app uses a single Ultra voice (Clara by default, configurable via `TTS_VOICE`) with `voice_settings.language_boost` set to the target language. Ultra supports 36+ languages — one voice covers all 8 target languages in this demo.

To use a different voice, enumerate available voices:

```bash
curl -H "Authorization: Bearer $TELNYX_API_KEY" \
  https://api.telnyx.com/v2/text-to-speech/voices \
  | jq '.voices[] | select(.id | startswith("Telnyx.Ultra."))'
```

TTS voice availability varies by language and provider. The default Ultra Clara voice is verified working for all 8 target languages with `language_boost`.

## Security Notes

- **API key never reaches the browser.** All Telnyx API calls are server-side.
- **Audio file size limit** enforced (default 25 MB).
- **MIME-type and extension validation** on uploads.
- **Safe filenames** for downloads (alphanumeric + dash/underscore only).
- **Request timeouts** on all Telnyx API calls.
- **No API keys in logs.** Transcripts and recordings are not logged by default.
- **In-memory store with TTL** (default 30 min). No database, no persistent storage.

## Known Limitations

- **In-memory storage.** Transcripts, translations, and audio expire after the TTL (default 30 min). Refresh the page and they're gone.
- **Single-user.** The app is designed for local demo use, not concurrent production traffic.
- **TTS text limit.** Maximum 3000 characters per TTS call (Telnyx API limit). Long translations should be chunked.
- **Translation model.** Kimi-K2.6 uses reasoning tokens. `max_tokens` is set to 2000 to ensure the translated content is returned (not just reasoning).
- **Audio format.** The browser records in WebM/Opus. For other formats, upload a file.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Missing or invalid `TELNYX_API_KEY` | Set `TELNYX_API_KEY` in `.env` |
| `400` from STT | Audio format not recognized | Ensure file has a recognized extension (.webm, .mp3, .wav, .m4a, .ogg, .flac) |
| `413` from STT | Audio file exceeds size limit | Reduce file size or increase `MAX_AUDIO_SIZE_MB` |
| `502` "STT returned empty transcript" | Audio too short or silent | Record at least 1 second of speech |
| `502` "Translation model returned empty content" | Translation model ran out of tokens | Keep source text under ~500 words |
| `502` from TTS | Text too long | Keep TTS text under 3000 characters |
| Browser mic not working | Permission denied | Check browser permissions for microphone access |
| Port 5000 already in use | macOS AirPlay Receiver | App defaults to `PORT=5050` |

## Related Examples

- [`ai-content-translator-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-content-translator-python) — STT + AI translate + TTS pipeline (file upload, same concept, different UI)
- [`multi-character-narrator-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/multi-character-narrator-python) — Multi-voice TTS with SSML emotions
- [`ai-voicemail-transcription-forwarding-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-voicemail-transcription-forwarding-python) — STT on phone voicemail audio
- [`voice-journal-daily-log-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/voice-journal-daily-log-python) — Phone-based voice journal with AI

## Agent Discovery

This example is part of the [Telnyx Code Examples](https://github.com/team-telnyx/telnyx-code-examples) catalog.

- **Agent signup**: [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md)
- **Agent CLI**: [github.com/team-telnyx/ai/tree/main/cli](https://github.com/team-telnyx/ai/tree/main/cli)
- **Agent skills**: [github.com/team-telnyx/ai/tree/main/skills](https://github.com/team-telnyx/ai/tree/main/skills)
- **Telnyx AI repo**: [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLM-optimized docs**: [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt)
- **Example index**: [`llms.txt`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/llms.txt)
- **Telnyx CLI (human)**: [developers.telnyx.com/development/cli](https://developers.telnyx.com/development/cli)

## Resources

- STT API: [developers.telnyx.com/api/inference/transcribe](https://developers.telnyx.com/api/inference/transcribe)
- Inference API: [developers.telnyx.com/api/inference/chat-completions](https://developers.telnyx.com/api/inference/chat-completions)
- TTS API: [developers.telnyx.com/api/inference/generate-speech-from-text](https://developers.telnyx.com/api/inference/generate-speech-from-text)
- Ultra TTS docs: [developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra](https://developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra)
- Voices API: `GET https://api.telnyx.com/v2/text-to-speech/voices`
- Repo CONTRIBUTING.md: [github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md](https://github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md)
