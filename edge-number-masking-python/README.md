---
name: edge-number-masking
title: "Edge Number Masking"
description: "Marketplace-style proxy number pool at the edge."
language: python
framework: flask
telnyx_products: [Edge Compute, Numbers, Voice, Call Recording]
channel: [voice]
---

# Edge Number Masking

> Also known as: number masking, proxy numbers, anonymous calling, marketplace phone masking.

Marketplace-style proxy number pool at the edge. Dynamically assigns masked number pairs per booking, routes calls bidirectionally through the proxy, records for dispute resolution, and auto-expires at checkout.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Transfer**: `POST /v2/calls/{id}/actions/transfer` -- [API reference](https://developers.telnyx.com/api/call-control/transfer-call)
- **Call Control: Reject**: `POST /v2/calls/{id}/actions/reject` -- [API reference](https://developers.telnyx.com/api/call-control/reject-call)
- **Call Control: Record Start**: `POST /v2/calls/{id}/actions/record_start` -- [API reference](https://developers.telnyx.com/api/call-control/start-recording)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.recording.saved` -- Recording available for download
- `call.hangup` -- Call ended, cleans up session state and logs outcome

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI model | [Models](https://developers.telnyx.com/docs/inference/models) |
| `PORT` | `integer` | `5000` | no | Server port | -- |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-number-masking-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

1. Expose your local server: `ngrok http 5000`
2. Configure in [Telnyx Portal](https://portal.telnyx.com/call-control/applications):
   - Call Control Application -> Webhook URL -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `POST /pool`

Pool.

```bash
curl -X POST http://localhost:5000/pool \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

**Response:**

```json
{"status": "ok"}
```

### `POST /bookings`

Bookings.

```bash
curl -X POST http://localhost:5000/bookings \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

**Response:**

```json
{"status": "ok"}
```

### `DELETE /bookings/<booking_id>`

<Booking Id>.

```bash
curl http://localhost:5000/bookings/<booking_id>
```

**Response:**

```json
{"status": "ok", "service": "edge-number-masking"}
```

### `GET /bookings`

Bookings.

```bash
curl http://localhost:5000/bookings
```

**Response:**

```json
{"status": "ok", "service": "edge-number-masking"}
```

### `GET /health`

Health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{"status": "ok", "service": "edge-number-masking"}
```


## Webhook Endpoints

### `POST /webhooks/voice`

Telnyx sends call events here. Your app processes them and responds with the next action.

**Events handled:**

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.recording.saved` -- Recording available for download
- `call.hangup` -- Call ended, cleans up session state and logs outcome

**Example payload:**

```json
{
  "data": {
    "event_type": "call.initiated",
    "id": "evt_123",
    "payload": {
      "call_control_id": "v3:abc123",
      "direction": "incoming",
      "from": "+12125551234",
      "to": "+18005559876"
    }
  }
}
```

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/pool` | Pool |
| `POST` | `/bookings` | Bookings |
| `DELETE` | `/bookings/<booking_id>` | <Booking Id> |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/bookings` | Bookings |
| `GET` | `/health` | Health |

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
