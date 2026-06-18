---
name: ai-video-dubbing-pipeline
title: "AI Video Dubbing Pipeline"
description: "Upload audio, STT transcribes with speaker diarization, AI Inference translates to target language, TTS generates dubbed audio with speaker-matched voices. Full STT-to-TTS pipeline."
language: python
framework: flask
telnyx_products: [AI Inference, Media Streaming]
integrations: []
channel: [voice, api]
---

# AI Video Dubbing Pipeline

Upload audio, STT transcribes with speaker diarization, AI Inference translates to target language, TTS generates dubbed audio with speaker-matched voices. Full STT-to-TTS pipeline.

## Telnyx API Endpoints Used

- **STT Transcribe**: `POST /v2/ai/transcribe` -- [ref](https://developers.telnyx.com/api/inference/transcribe)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [ref](https://developers.telnyx.com/api/inference/chat-completions)
- **TTS Generate**: `POST /v2/ai/generate` -- [ref](https://developers.telnyx.com/api/inference/generate)

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ AI Inference      │ ── translate + adapt tone
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ TTS Generation    │ ── render audio
  │ (multiple takes/  │
  │  voices/languages)│
  └────────┬─────────┘
           │
           ├──► Voice response
           └──► Download / stream
```

## How It Works

1. Sends conversation to Telnyx AI Inference for processing
2. Converts response to speech via Telnyx TTS

## Why Telnyx

- **Co-located inference** — LLM runs on the same network as voice traffic. Sub-200ms round trips.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|------------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI Inference model | [Docs](https://developers.telnyx.com/docs/inference/models) |
| `TTS_MODEL` | `string` | `telnyx/tts` | no | TTS model name | [Docs](https://developers.telnyx.com/docs/inference) |
| `STT_MODEL` | `string` | `telnyx/asr` | no | STT model name | [Docs](https://developers.telnyx.com/docs/inference) |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-video-dubbing-pipeline-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

```bash
ngrok http 5000
```

Set webhook URL in [Telnyx Portal](https://portal.telnyx.com):
- Call Control Application -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `POST /dub`

Upload as multipart form:

```bash
curl -X POST http://localhost:5000/dub \
  -F audio=@episode.mp3 \
  -F target_language=es \
  -F source_language=en
```

**Response:**

```json
{"job_id": "dub-a1b2c3d4", "status": "complete", "segments_dubbed": 12, "speakers": 3, "speaker_voice_map": {"SPEAKER_0": "onyx", "SPEAKER_1": "nova"}}
```

### `GET /health`

```bash
curl http://localhost:5000/health
```

```json
{"status": "ok"}
```

## Troubleshooting

- **Connection refused on port 5000**: App isn't running. Run `python app.py` and check no other process uses port 5000.
- **401 Unauthorized**: Your `TELNYX_API_KEY` is invalid. Generate a new one at [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys).
- **AI response slow/empty**: Verify model name. See available models at [developers.telnyx.com](https://developers.telnyx.com/docs/inference/list-models).

## Related Examples

- [run-llm-inference-python](../run-llm-inference-python/) - Standalone inference
- [build-voice-ai-agent-python](../build-voice-ai-agent-python/) - Voice AI agent

## Resources

- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
