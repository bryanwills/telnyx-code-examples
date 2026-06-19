# Route Inbound Phone Calls with Telnyx and Go

Receive inbound call webhooks from the Telnyx Voice API and answer calls programmatically with a Go + Gin server.

## How It Works

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

## Telnyx Products Used

- **Voice (Call Control)** — receive call lifecycle webhooks and issue commands like answer

## API Endpoints

- **Answer Call**: `POST /v2/calls/{call_control_id}/actions/answer` -- [API reference](https://developers.telnyx.com/api-reference/calls/answer-call)

## Prerequisites

- Go 1.22+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- A Call Control Application with a webhook URL configured
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/route-phone-calls-to-ai-agent-go
cp .env.example .env
go mod download
```

Edit `.env` and set your `TELNYX_API_KEY`. Optionally set `PORT` (the server defaults to `8080` if unset).

## Step 2: Understand the Code

Everything lives in `main.go`. Here's what each piece does.

### Routes

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness probe, returns `{"status":"ok"}` |
| `POST` | `/webhooks/call` | Receives Telnyx Call Control webhook events |

### `main()`

Initializes the Telnyx client from `TELNYX_API_KEY`, builds a Gin router with request logging, registers the two routes, then starts the server on `PORT` (default `8080`).

```go
client := telnyx.NewClient(option.WithAPIKey(os.Getenv("TELNYX_API_KEY")))
router := gin.Default()
router.GET("/health", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"status": "ok"}) })
router.POST("/webhooks/call", func(c *gin.Context) { handleCallWebhook(c, client) })
```

### `handleCallWebhook()`

Binds the incoming JSON to a `WebhookPayload`, logs the key fields, then switches on `data.event_type` and dispatches to a per-event handler. An unparseable body returns `400`.

### Event handlers

- **`handleCallInitiated()`** — fires when an inbound call arrives. It issues the Answer Call command via `client.Calls.Answer(&telnyx.CallAnswerParams{CallControlID: callControlID})`. On failure it returns `500`; on success it returns `200` with `{"message": "Call answered", ...}`.
- **`handleCallAnswered()`** — acknowledges the connected call. A natural place to start recording, play a greeting, or route to an IVR.
- **`handleCallHangup()`** — acknowledges teardown and logs the `disconnect_code`.
- **`handleDTMFReceived()`** — acknowledges a pressed digit, for IVR or PIN-entry logic.

## Step 3: Run It

```bash
go run .
```

The server starts on the `PORT` from `.env` (default `http://localhost:8080`).

In a separate terminal, expose your server for webhooks (use your `PORT`):

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Call Control App** → Webhook URL → `https://<id>.ngrok.io/webhooks/call`
- Assign your inbound phone number to that Call Control App.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Simulate an inbound call event:**

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

Or call your Telnyx number to trigger the real webhook flow.

## Going to Production

- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Persistence** — log call metadata (start/answer/end times, disconnect codes) to a database
- **Routing logic** — extend the event handlers to screen calls, gather DTMF for an IVR, or hand off to an AI agent
- **Monitoring** — add structured logging and alert on `/health`
- **Rate limiting** — protect the webhook endpoint from abuse

## Run

```bash
go mod download
go run .
```

## Resources

- [Source code and reference](./README.md)
- [Typed endpoint reference](./API.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Voice API Overview](https://developers.telnyx.com/docs/voice)
- [Telnyx Go SDK](https://developers.telnyx.com/development/sdk/go)
- [Telnyx Portal](https://portal.telnyx.com)
