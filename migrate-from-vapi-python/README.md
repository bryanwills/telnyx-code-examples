---
name: migrate-from-vapi
title: "Migrate from Vapi"
description: "Migrate from Vapi — import Vapi voice agents to Telnyx AI Assistants with voice, prompt, and tool configuration mapping."
language: python
framework: flask
telnyx_products: [Migration, Number Porting]
channel: [voice]
---

# Migrate from Vapi

Migrate from Vapi — import Vapi voice agents to Telnyx AI Assistants with voice, prompt, and tool configuration mapping.

## Telnyx API Endpoints Used

- **Create AI Assistant**: `POST /v2/ai/assistants` — [API reference](https://developers.telnyx.com/api/ai-assistants/create-assistant)
- **Chat Completions**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Architecture

```text
┌─────────────┐     ┌────────────┐     ┌──────────────────────┐
│ Phone Call   │────►│   Telnyx   │────►│ POST /webhooks/voice │
└─────────────┘     │   Cloud    │     └──────────┬───────────┘
                    └────────────┘                │
                                           TTS response
                                           back to caller
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `VAPI_API_KEY` | `string` | `your_value` | **yes** | Vapi api key | — |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/migrate-from-vapi-python
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

### Docker

```bash
docker build -t migrate-from-vapi-python .
docker run --env-file .env -p 5000:5000 migrate-from-vapi-python
```

## API Reference

### `GET /audit/vapi`

Returns vapi

```bash
curl http://localhost:5000/audit/vapi
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

### `POST /migrate/agent`

Triggers agent

```bash
curl -X POST http://localhost:5000/migrate/agent \
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

### `GET /mapping/models`

Returns models

```bash
curl http://localhost:5000/mapping/models
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
