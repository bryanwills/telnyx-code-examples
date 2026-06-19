# Receive Your First Inbound SMS with Telnyx and Express

Build a production-ready Express server that receives inbound SMS messages via Telnyx webhooks. Validates payloads and acknowledges within 5 seconds.

## How It Works

```
  Inbound SMS
        │
        ▼
  ┌──────────────────┐
  │ Telnyx Messaging  │
  └────────┬─────────┘
           │ POST webhook
           ▼
  ┌──────────────────┐
  │ Express server    │
  │ /webhooks/sms     │
  └────────┬─────────┘
           │
           └──► validate → store → 200 OK
```

## Telnyx Products Used

- **Messaging** — send and receive messages with delivery receipts

## API Endpoints

- **Inbound Message webhook**: `POST /webhooks/sms` (your endpoint, called by Telnyx) -- [Webhook reference](https://developers.telnyx.com/docs/messaging/messages/receive-message)

## Prerequisites

- Node.js 14+
- [Telnyx account](https://portal.telnyx.com/sign-up)
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) enabled for inbound SMS
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with an inbound webhook URL
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/receive-sms-webhook-nodejs
cp .env.example .env
npm install
```

Edit `.env` with your Telnyx credentials. `TELNYX_API_KEY` initializes the SDK client; `PORT` controls the listen port (defaults to `3000` if unset, the example sets it to `5000`).

## Step 2: Understand the Code

Everything lives in `server.js`. Here's what each piece does.

### Helper Function

- **`processInboundSMS(payload)`** — Validates the webhook envelope and pulls message fields out of `payload.data.payload`. Throws if the structure is wrong or if sender/recipient numbers are missing.

```javascript
function processInboundSMS(payload) {
  if (!payload.data || !payload.data.payload) {
    throw new Error("Invalid webhook payload structure");
  }

  const messageData = payload.data.payload;

  const processedMessage = {
    message_id: messageData.id || null,
    from: messageData.from?.phone_number || null,
    to: messageData.to?.[0]?.phone_number || null,
    text: messageData.text || "",
    received_at: messageData.received_at || new Date().toISOString(),
    direction: messageData.direction || "inbound",
  };

  if (!processedMessage.from || !processedMessage.to) {
    throw new Error("Missing sender or recipient phone number in webhook");
  }

  return processedMessage;
}
```

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/sms` | Receive inbound SMS events from Telnyx |
| `GET` | `/messages` | View stored messages (debug; remove in production) |
| `GET` | `/health` | Health check |

The webhook handler validates the body, processes the message, stores it, and acknowledges with `200` so Telnyx stops retrying:

```javascript
app.post("/webhooks/sms", (req, res) => {
  try {
    if (!req.body || !req.body.data) {
      return res.status(400).json({ error: "Invalid webhook payload" });
    }

    const message = processInboundSMS(req.body);
    receivedMessages.push(message);

    res.status(200).json({
      success: true,
      message_id: message.message_id,
      status: "received",
    });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});
```

Received messages are kept in an in-memory array. Swap this for a database in production.

## Step 3: Run It

```bash
node server.js
```

Server starts on `http://localhost:5000` (or `3000` if `PORT` is unset).

In a separate terminal, expose your server for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Settings → Webhook URL → `https://<id>.ngrok.io/webhooks/sms`

Then assign your inbound-enabled number to that Messaging Profile.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Simulate an inbound webhook:**

```bash
curl -X POST http://localhost:5000/webhooks/sms \
  -H "Content-Type: application/json" \
  -d '{"data":{"event_type":"message.received","payload":{"id":"msg-1","from":{"phone_number":"+12125551234"},"to":[{"phone_number":"+13125559876"}],"text":"Hello"}}}'
```

**View what was received:**

```bash
curl http://localhost:5000/messages
```

Or text your Telnyx number from a real phone and watch the server logs print the inbound message.

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory `receivedMessages` array with PostgreSQL or Redis
- **Authentication** — restrict the `/messages` debug endpoint or remove it
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Fast acknowledgment** — respond `200` immediately and move heavy work (DB writes, downstream calls) to a background queue so you stay under the 5-second window
- **Monitoring** — add structured logging and health check alerts

## Run

```bash
npm install
node server.js
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message)
- [Telnyx Portal](https://portal.telnyx.com)
