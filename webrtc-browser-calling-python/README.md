---
description: Browser-to-PSTN calling with WebRTC, credential management, and call
  control.
framework: flask
language: python
name: webrtc-browser-calling
telnyx_products:
- Voice
- WebRTC
title: Production-ready WebRTC calling application with Telnyx Voice API and FastAPI.
---


# Production-ready WebRTC calling application with Telnyx Voice API and FastAPI.

Voice application. Built with Telnyx Migration, Number Porting, Voice, WebRTC.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `call.answered` — Call connected — app begins interaction
- `call.dtmf.received` — DTMF tone detected during call
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.initiated` — New inbound or outbound call detected

## Architecture

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Call Control      │
  └────────┬─────────┘
           │
           ├──► DTMF
           │
           ▼
     Call completed
```

## How It Works

1. Receives incoming call via Telnyx Call Control webhook
2. Transfers call to human agent when needed

## Why Telnyx

- **Single-vendor voice stack** — call control, STT, TTS, and recording from one API. No multi-vendor coordination.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `TELNYX_PHONE_NUMBER` | `string` | `your_value` | **yes** | Telnyx phone number | — |
| `TELNYX_CONNECTION_ID` | `string` | `your_value` | **yes** | Telnyx connection id | — |
| `WEBHOOK_URL` | `string` | `https://your-server.example.com` | no | Public URL for receiving webhooks | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/webrtc-browser-calling-python
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

## Testing

**Get WebRTC credentials:**

```bash
curl http://localhost:5000/api/credentials
```

**Response:**

```json
{"sip_username": "user@sip.telnyx.com", "credential_id": "<value>", "status": "ok"}
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Resources

- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## API Reference

### `GET /health`

Health check endpoint.

```bash
curl http://localhost:5000/health
```

```json
{"status": "ok"}
```
