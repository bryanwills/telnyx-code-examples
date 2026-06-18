---
name: ivr-prompt-generator
title: "IVR Prompt Generator"
description: "Generate professional IVR/phone system prompts. AI writes caller-friendly scripts from business descriptions, TTS renders in multiple voices, test via live Telnyx call playback."
language: python
framework: flask
telnyx_products: [Voice, AI Inference, Cloud Storage]
---

# IVR Prompt Generator

Generate professional IVR/phone system prompts. AI writes caller-friendly scripts from business descriptions, TTS renders in multiple voices, test via live Telnyx call playback.

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `call.answered` — Call connected — app begins interaction (TTS greeting, gather)
- `call.speak.ended` — TTS playback finished — app transitions to next action (gather, transfer, etc.)

## External Service Integrations

- **Email / SMTP** — Email notifications and alerts

## Architecture

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Answer + Greet    │ ── TTS welcome message
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Listen for Input  │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ AI Inference      │
  │ • Business logic   │
  └────────┬─────────┘
           │ ◄──── conversation loop
           │
           ├──► Voice response
           ├──► Email
           └──► Cloud Storage
```

## Telnyx API Endpoints Used

- **AI Inference (script writing)**: `POST /v2/ai/chat/completions` -- [ref](https://developers.telnyx.com/api/inference/chat-completions)
- **TTS Generate**: `POST /v2/ai/generate` -- [ref](https://developers.telnyx.com/api/inference/generate)
- **Create Call (preview)**: `POST /v2/calls` -- [ref](https://developers.telnyx.com/api/call-control/create-call)
- **Speak (playback)**: `POST /v2/calls/{id}/actions/speak` -- [ref](https://developers.telnyx.com/api/call-control/speak)
- **Cloud Storage**: `PUT https://storage.telnyx.com/{bucket}/{key}` -- [docs](https://developers.telnyx.com/docs/cloud-storage)

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|------------------|
| `TELNYX_API_KEY` | `string` | `KEY...` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `MAIN_NUMBER` | `string` | `+18005551234` | **yes** | Telnyx phone number (E.164) | [Portal](https://portal.telnyx.com/numbers/my-numbers) |
| `CONNECTION_ID` | `string` | `149...` | **yes** | Call Control connection ID | [Portal](https://portal.telnyx.com/call-control/applications) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI Inference model | [Docs](https://developers.telnyx.com/docs/inference/models) |
| `TTS_MODEL` | `string` | `telnyx/tts` | no | TTS model | [Docs](https://developers.telnyx.com/docs/inference) |
| `BUCKET_NAME` | `string` | `voiceovers` | no | Cloud Storage bucket | [Portal](https://portal.telnyx.com/storage) |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ivr-prompt-generator-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

1. Expose your local server:

   ```bash
   ngrok http 5000
   ```

2. Copy the HTTPS URL and configure in [Telnyx Portal](https://portal.telnyx.com):

   - **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`
   - **Messaging Profile** → Inbound Webhook URL → `https://<id>.ngrok.io/webhooks/sms`

### Docker

```bash
docker build -t ivr-prompt-generator-python .
docker run --env-file .env -p 5000:5000 ivr-prompt-generator-python
```

## API Reference

### `POST /prompts/generate`

```bash
curl -X POST http://localhost:5000/prompts/generate \
  -H "Content-Type: application/json" \
  -d '{"business_name": "Acme Corp", "business_type": "SaaS", "departments": ["Sales", "Support", "Billing"]}'
```

**Response:**

```json
{"set_id": "ivr-a1b2c3d4", "prompts_generated": 8, "voice": "nova"}
```

### `GET /health`

```bash
curl http://localhost:5000/health
```

```json
{"status": "ok"}
```

## Webhook Endpoints

### `POST /webhooks/voice`

Handles Telnyx Call Control webhook events. Called automatically by Telnyx — do not call directly.

## Resources

- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Cloud Storage Docs](https://developers.telnyx.com/docs/cloud-storage)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
