---
name: route-phone-calls-to-ai-agent
title: "Route Phone Calls to AI Agent"
description: "Receive inbound call webhooks from the Telnyx Voice API and answer calls programmatically with a Go + Gin server."
language: go
framework: gin
telnyx_products: [Voice]
channel: [voice]
---

# Route Phone Calls to AI Agent

Receive inbound call webhooks from the Telnyx Voice API and answer calls programmatically with a Go + Gin server.

## Telnyx API Endpoints Used

- **Answer Call**: `POST /v2/calls/{call_control_id}/actions/answer` -- [API reference](https://developers.telnyx.com/api-reference/calls/answer-call)

## Architecture

```
  Inbound Call
        │
        ▼
  ┌──────────────────┐
  │  Telnyx Voice     │
  │  (Call Control)   │
  └────────┬─────────┘
           │  webhook (call.initiated, call.answered,
           │           call.hangup, call.dtmf.received)
           ▼
  ┌──────────────────┐
  │  Gin server       │
  │  POST /webhooks/  │
  │       call        │
  └────────┬─────────┘
           │  Answer Call command
           └──► Telnyx Voice API
```

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.

- **Call Control built in** — receive structured webhook events for every stage of a call and issue commands like answer, hangup, and DTMF gather over a single API.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY_your_telnyx_api_key_here` | **yes** | Telnyx API v2 key used to authenticate Call Control commands | [Portal](https://portal.telnyx.com/api-keys) |
| `PORT` | `string` | `5000` | no | Port the Gin server listens on. Defaults to `8080` when unset | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/route-phone-calls-to-ai-agent-go
cp .env.example .env    # ← fill in your credentials
go mod download
go run .                # starts on the PORT from .env (default 8080)
```

### Webhook Configuration

1. Expose your local server (replace `5000` with your `PORT` value):

   ```bash
   ngrok http 5000
   ```

2. Copy the HTTPS URL and configure it in the [Telnyx Portal](https://portal.telnyx.com):

   - **Call Control App** → Webhook URL → `https://<id>.ngrok.io/webhooks/call`
   - Assign your inbound phone number to that Call Control App.

## API Reference

### `GET /health`

Liveness probe. Returns `200` when the server is running.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok"
}
```

### `POST /webhooks/call`

Receives Telnyx Call Control webhook events. The handler inspects `data.event_type` and acts on it:

- `call.initiated` — answers the call via the Telnyx Voice API.
- `call.answered` — acknowledges the connected call.
- `call.hangup` — acknowledges call teardown.
- `call.dtmf.received` — acknowledges a pressed digit.
- Any other event type — acknowledged with a generic message.

```bash
curl -X POST http://localhost:5000/webhooks/call \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "event_type": "call.initiated",
      "call_control_id": "v3:abc123",
      "from": "+12125551234",
      "to": "+13105559876"
    }
  }'
```

**Response (for `call.initiated`):**

```json
{
  "message": "Call answered",
  "call_control_id": "v3:abc123"
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `Invalid JSON payload` (400) | Request body is missing or does not match the expected `{ "data": { ... } }` shape. | Send a well-formed Telnyx webhook payload. Test with the `curl` example above to isolate the issue. |
| Webhook never fires | The webhook URL in the Portal does not match your public URL. | Confirm the Call Control App webhook URL is your ngrok HTTPS URL plus `/webhooks/call`, and that your number is assigned to that app. |
| `Failed to answer call` (500) | `TELNYX_API_KEY` is missing or invalid, so the Answer Call command is rejected. | Set a valid key from [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys) in `.env` and restart with `go run .`. |
| Connection refused | The server is not listening on the port you are calling. | The server uses `PORT` from `.env` (default `8080`). Match your `curl`/ngrok port to that value. |

## Related Examples

- [route-phone-calls-to-ai-agent-python](../route-phone-calls-to-ai-agent-python/) - Same example in Python
- [route-phone-calls-to-ai-agent-nodejs](../route-phone-calls-to-ai-agent-nodejs/) - Same example in Node.js
- [send-sms-go](../send-sms-go/) - Send an SMS with the Telnyx Go SDK and Gin

## Resources

- [Voice API Overview](https://developers.telnyx.com/docs/voice)
- [Answer Call API Reference](https://developers.telnyx.com/api-reference/calls/answer-call)
- [Telnyx Go SDK](https://developers.telnyx.com/development/sdk/go)
- [Telnyx Voice (Voice AI Agents)](https://telnyx.com/products/voice-ai-agents)
- [Voice Pricing](https://telnyx.com/pricing/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
