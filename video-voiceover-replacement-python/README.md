---
name: video-voiceover-replacement
title: "Video Voice-Over Replacement"
description: "Upload audio with existing voice-over. STT extracts the script, AI rewrites/improves it (5 modes: polish, professional, simplify, energize, shorten), TTS re-records with studio quality."
language: python
framework: flask
telnyx_products: [AI Inference, Media Streaming, Cloud Storage]
---

# Video Voice-Over Replacement

Upload audio with existing voice-over. STT extracts the script, AI rewrites/improves it (5 modes: polish, professional, simplify, energize, shorten), TTS re-records with studio quality.

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ AI Inference      │ ── direction cues, rewrites
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ TTS Generation    │ ── render audio
  │ (multiple takes/  │
  │  voices/languages)│
  └────────┬─────────┘
           │
           ├──► Cloud Storage
           └──► Cloud Storage (final assets)
```

## Telnyx API Endpoints Used

- **STT Transcribe**: `POST /v2/ai/transcribe` -- [ref](https://developers.telnyx.com/api/inference/transcribe)
- **AI Inference (rewrite)**: `POST /v2/ai/chat/completions` -- [ref](https://developers.telnyx.com/api/inference/chat-completions)
- **TTS Generate**: `POST /v2/ai/generate` -- [ref](https://developers.telnyx.com/api/inference/generate)
- **Cloud Storage (S3-compatible)**: `s3.put_object(...)` via boto3 against `https://{region}.telnyxcloudstorage.com` -- [docs](https://developers.telnyx.com/docs/cloud-storage)

## How It Works

1. Sends conversation to Telnyx AI Inference for processing
2. Converts response to speech via Telnyx TTS
3. Stores the rendered audio in Telnyx Cloud Storage (S3-compatible) with boto3 and returns a presigned GET URL

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.

- **Co-located inference** — LLM runs on the same network as voice traffic. Sub-200ms round trips.
- **Integrated storage** — S3-compatible Cloud Storage co-located with voice and AI infrastructure. Talk to it with the AWS SDK (boto3) and hand out time-limited presigned URLs.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|------------------|
| `TELNYX_API_KEY` | `string` | `KEY...` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI Inference model | [Docs](https://developers.telnyx.com/docs/inference/models) |
| `TTS_MODEL` | `string` | `telnyx/tts` | no | TTS model | [Docs](https://developers.telnyx.com/docs/inference) |
| `STT_MODEL` | `string` | `telnyx/asr` | no | STT model | [Docs](https://developers.telnyx.com/docs/inference) |
| `BUCKET_NAME` | `string` | `voiceovers` | no | Cloud Storage bucket | [Portal](https://portal.telnyx.com/storage) |
| `TELNYX_STORAGE_REGION` | `string` | `us-central-1` | no | Cloud Storage region (selects the S3 endpoint host); options: `us-central-1`, `us-east-1`, `us-west-1`, `eu-central-1` | [Docs](https://developers.telnyx.com/docs/cloud-storage) |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/video-voiceover-replacement-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

## API Reference

### `POST /replace`

Upload as multipart form:

```bash
curl -X POST http://localhost:5000/replace \
  -F audio=@input.mp3 \
  -F mode=professional
```

**Response:**

```json
{"job_id": "rep-a1b2c3d4", "mode": "professional", "original_word_count": 234, "improved_word_count": 218, "change_pct": -6.8}
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
- [Cloud Storage Docs](https://developers.telnyx.com/docs/cloud-storage)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
