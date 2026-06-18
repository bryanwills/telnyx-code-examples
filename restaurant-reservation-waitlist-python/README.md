---
name: restaurant-reservation-waitlist
title: "Restaurant Reservation & Waitlist"
description: "AI answers calls, checks table availability, books or adds to waitlist, texts when table is ready. Host reviews large party requests."
language: python
framework: flask
telnyx_products: [Voice, AI Inference]
integrations: [Slack]
channel: [voice]
---

# Restaurant Reservation & Waitlist

AI answers calls, checks table availability, books or adds to waitlist, texts when table is ready. Host reviews large party requests.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Gather (STT/DTMF)**: `POST /v2/calls/{id}/actions/gather_using_speak` — [API reference](https://developers.telnyx.com/api/call-control/gather)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` — [API reference](https://developers.telnyx.com/api/call-control/speak)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `call.answered` — Call connected — app begins interaction
- `call.gather.ended` — Caller input received (speech transcription or DTMF digits)
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.initiated` — New inbound or outbound call detected
- `call.speak.ended` — TTS playback finished — app transitions to next action (gather, transfer, etc.)

## External Service Integrations

- **Slack** — Team notifications via incoming webhooks ([docs](https://api.slack.com/messaging/webhooks))

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
  │ Gather Speech     │ ── STT transcription
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ AI Inference      │
  │ • Appointment scheduling│
  │ • Queue management │
  └────────┬─────────┘
           │ ◄──── conversation loop
           │
           ├──► SMS notification
           ├──► Voice response
           └──► Slack alert

  State: In-memory dict
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `MAIN_NUMBER` | `string` | `+18005551234` | **yes** | Telnyx phone number (E.164) | [Portal](https://portal.telnyx.com/numbers/my-numbers) |
| `CONNECTION_ID` | `string` | `1494404757140276705` | **yes** | Call Control connection/app ID | [Portal](https://portal.telnyx.com/call-control/applications) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | Telnyx AI Inference model name | [Portal](https://developers.telnyx.com/docs/inference/models) |
| `HOST_SLACK_WEBHOOK` | `string` | `your_value` | **yes** | Host slack webhook | — |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/restaurant-reservation-waitlist-python
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
docker build -t restaurant-reservation-waitlist-python .
docker run --env-file .env -p 5000:5000 restaurant-reservation-waitlist-python
```

## API Reference

### `POST /waitlist/add`

Triggers add

```bash
curl -X POST http://localhost:5000/waitlist/add \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "reservations": [
    {
      "id": "res-001",
      "name": "Johnson",
      "party_size": 4,
      "time": "19:30",
      "status": "confirmed"
    }
  ]
}
```

### `POST /waitlist/<int:idx>/ready`

Triggers ready

```bash
curl -X POST http://localhost:5000/waitlist/<int:idx>/ready \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "reservations": [
    {
      "id": "res-001",
      "name": "Johnson",
      "party_size": 4,
      "time": "19:30",
      "status": "confirmed"
    }
  ]
}
```

### `GET /reservations`

Returns reservations

```bash
curl http://localhost:5000/reservations
```

**Response:**

```json
{
  "reservations": [
    {
      "id": "res-001",
      "name": "Johnson",
      "party_size": 4,
      "time": "19:30",
      "status": "confirmed"
    }
  ]
}
```

### `GET /waitlist`

Returns waitlist

```bash
curl http://localhost:5000/waitlist
```

**Response:**

```json
{
  "reservations": [
    {
      "id": "res-001",
      "name": "Johnson",
      "party_size": 4,
      "time": "19:30",
      "status": "confirmed"
    }
  ]
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

### `POST /webhooks/voice`

Receives [Telnyx Call Control](https://developers.telnyx.com/docs/voice/call-control) webhook events.

**Events handled:** `call.answered`, `call.gather.ended`, `call.hangup`, `call.initiated`, `call.speak.ended`

**Example payload:**

```json
{
  "data": {
    "event_type": "call.gather.ended",
    "id": "a1b2c3d4-5678-9abc-def0-123456789abc",
    "occurred_at": "2026-07-15T14:30:15.000Z",
    "payload": {
      "call_control_id": "v3:uMi2qMWHT-mLFGkEm4t9tA",
      "connection_id": "1494404757140276705",
      "client_state": "eyJzdGVwIjoibWFpbl9tZW51In0=",
      "digits": "1",
      "from": "+12125551234",
      "to": "+13105559876",
      "speech": {
        "result": "I need help with my account billing",
        "confidence": 0.94
      },
      "status": "valid"
    },
    "record_type": "event"
  }
}
```

## Resources

- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
