---
name: ai-powered-ivr-replacement
title: "AI-Powered IVR Replacement"
description: "AI-Powered IVR Replacement — natural language routing with A/B testing and structured insights."
language: python
framework: flask
telnyx_products: [Voice AI, AI Assistants]
---

# AI-Powered IVR Replacement

AI-Powered IVR Replacement — natural language routing with A/B testing and structured insights.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `ai.assistant.insights` — AI Assistant generated insights from conversation
- `call.initiated` — New inbound or outbound call detected

## Architecture

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Telnyx AI         │ ── managed assistant handles call
  │ Assistants API    │
  └────────┬─────────┘
           │
           ├──► A/B test routing (version A vs B)
           │
           ▼
  ┌──────────────────┐
  │ Natural Language  │ ── voice-driven menu, no DTMF trees
  │ Call Routing      │
  └────────┬─────────┘
           │
           ├──► Transfer to department
           ├──► Self-service resolution
           └──► Voicemail fallback
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `ASSISTANT_ID` | `string` | `asst_abc123` | no | Telnyx AI Assistant ID | [Portal](https://portal.telnyx.com/ai/assistants) |
| `FLASK_DEBUG` | `string` | `false` | no | Flask debug | — |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-powered-ivr-replacement-python
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
docker build -t ai-powered-ivr-replacement-python .
docker run --env-file .env -p 5000:5000 ai-powered-ivr-replacement-python
```

## API Reference

### `POST /setup`

One-time setup: create the AI assistant with A/B test configuration.

```bash
curl -X POST http://localhost:5000/setup \
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

### `GET /analytics`

Get IVR replacement analytics and A/B test results.

```bash
curl http://localhost:5000/analytics
```

**Response:**

```json
{
  "period": "2026-07-15",
  "total_calls": 1247,
  "avg_duration_seconds": 186,
  "inbound": 823,
  "outbound": 424,
  "peak_hour": "14:00",
  "cost_usd": 42.18
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

## Webhook Endpoints

### `POST /webhooks/assistant`

Receives Telnyx webhook events for `/webhooks/assistant`.

## Resources

- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
