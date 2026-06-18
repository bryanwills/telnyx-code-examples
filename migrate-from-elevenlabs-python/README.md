---
name: migrate-from-elevenlabs
title: "Migrate from ElevenLabs"
description: "Migrate from ElevenLabs — import ElevenLabs voice configurations to Telnyx TTS with voice mapping and cost comparison."
language: python
framework: flask
telnyx_products: [AI Assistants, Migration]
channel: [voice]
---

# Migrate from ElevenLabs

Migrate from ElevenLabs — import ElevenLabs voice configurations to Telnyx TTS with voice mapping and cost comparison.

## Telnyx API Endpoints Used

- **TTS Generate**: `POST /v2/ai/generate` — [API reference](https://developers.telnyx.com/api/inference/generate)
- **Chat Completions**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **List Models**: `GET /v2/ai/models` — [API reference](https://developers.telnyx.com/api/inference/list-models)

## Architecture

```
  ElevenLabs (source)
        │
        ▼
  ┌──────────────────┐     ┌───────────────────┐
  │ 1. Audit         │────►│ Inventory Report  │
  │    (numbers,     │     │ (numbers, configs,│
  │     configs)     │     │  webhooks, apps)  │
  └────────┬─────────┘     └───────────────────┘
           │
           ▼
  ┌──────────────────┐
  │ 2. Map Features  │ ── source capability → Telnyx equivalent
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐     ┌───────────────────┐
  │ 3. Provision     │────►│ Telnyx Platform   │
  │    on Telnyx     │     │ • Phone numbers   │
  └────────┬─────────┘     │ • SIP connections │
           │               │ • Messaging       │
           ▼               └───────────────────┘
  ┌──────────────────┐
  │ Migration Report │
  │ (success/fail    │
  │  per resource)   │
  └──────────────────┘
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `ELEVENLABS_API_KEY` | `string` | `your_value` | **yes** | Elevenlabs api key | — |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/migrate-from-elevenlabs-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

### Webhook Configuration

1. Expose your local server:

   ```bash
   ngrok http 5000
   ```

2. Copy the HTTPS URL and configure in [Telnyx Portal](https://portal.telnyx.com):

   - **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `GET /audit/elevenlabs`

Returns elevenlabs

```bash
curl http://localhost:5000/audit/elevenlabs
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `POST /migrate/voice-config`

Triggers voice-config

```bash
curl -X POST http://localhost:5000/migrate/voice-config \
  -H "Content-Type: application/json" \
  -d '{
    "source_api_key": "SK_twilio_xxx",
    "dry_run": true
  }'
```

**Response:**

```json
{
  "migration": {
    "status": "completed",
    "resources_migrated": 12,
    "phone_numbers": 5,
    "applications": 3,
    "messaging_profiles": 2,
    "webhooks": 2
  }
}
```

### `GET /mapping/voices`

Returns voices

```bash
curl http://localhost:5000/mapping/voices
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /cost-comparison`

Returns cost-comparison

```bash
curl http://localhost:5000/cost-comparison
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `POST /test-tts`

Triggers test-tts

```bash
curl -X POST http://localhost:5000/test-tts \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `GET /migration-log`

Returns migration-log

```bash
curl http://localhost:5000/migration-log
```

**Response:**

```json
{
  "migration": {
    "status": "completed",
    "resources_migrated": 12,
    "phone_numbers": 5,
    "applications": 3,
    "messaging_profiles": 2,
    "webhooks": 2
  }
}
```

### `GET /health`

Returns health

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "uptime_seconds": 3842,
  "active_sessions": 2,
  "version": "1.0.0"
}
```

## Resources

- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
