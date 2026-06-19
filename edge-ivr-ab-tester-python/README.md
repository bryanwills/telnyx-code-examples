---
name: edge-ivr-ab-tester
title: "Edge IVR A/B Tester"
description: "A/B test different IVR flows at the edge."
language: python
framework: flask
telnyx_products: [Edge Compute, Voice, AI Inference]
channel: [voice]
---

# Edge IVR A/B Tester

> Also known as: IVR testing, A/B test phone menu, call flow optimization, IVR analytics.

A/B test different IVR flows at the edge. Randomly assigns callers to variants, tracks completion rates per variant, and auto-promotes the winner when statistical significance is reached.

## Telnyx API Endpoints Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.gather.ended` -- Caller input received (speech or DTMF), app processes response
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
cd telnyx-code-examples/edge-ivr-ab-tester-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

1. Expose your local server: `ngrok http 5000`
2. Configure in [Telnyx Portal](https://portal.telnyx.com/call-control/applications):
   - Call Control Application -> Webhook URL -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `POST /experiments`

Experiments.

```bash
curl -X POST http://localhost:5000/experiments \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

**Response:**

```json
{"status": "ok"}
```

### `GET /experiments`

Experiments.

```bash
curl http://localhost:5000/experiments
```

**Response:**

```json
{"status": "ok", "service": "edge-ivr-ab-tester"}
```

### `GET /experiments/<exp_id>`

<Exp Id>.

```bash
curl http://localhost:5000/experiments/<exp_id>
```

**Response:**

```json
{"status": "ok", "service": "edge-ivr-ab-tester"}
```

### `GET /health`

Health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{"status": "ok", "service": "edge-ivr-ab-tester"}
```


## Webhook Endpoints

### `POST /webhooks/voice`

Telnyx sends call events here. Your app processes them and responds with the next action.

**Events handled:**

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.gather.ended` -- Caller input received (speech or DTMF), app processes response
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
| `POST` | `/experiments` | Experiments |
| `GET` | `/experiments` | Experiments |
| `GET` | `/experiments/<exp_id>` | <Exp Id> |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/health` | Health |

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
