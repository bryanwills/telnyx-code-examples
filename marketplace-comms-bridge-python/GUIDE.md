# Marketplace Comms Bridge

> Buyer texts about a listing, AI responds with details, facilitates anonymous buyer-seller connection via masked numbers, handles scheduling. Ops reviews flagged conversations.

## What You'll Build

A production-ready **marketplace comms bridge** built with Python, Flask, and AI Inference.

Integrates with Slack for extended functionality.

| | |
|---|---|
| **Lines of code** | 92 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | AI Inference |
| **Channels** | sms |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [Slack webhook URL](https://api.slack.com/messaging/webhooks)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Webhook Events Handled

This app handles these [Messaging](https://developers.telnyx.com/docs/api/v2/messaging) webhook events:
- `message.received` -- Inbound SMS/MMS received
- `message.sent` -- Outbound message accepted by carrier
- `message.finalized` -- Final delivery status

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/marketplace-comms-bridge-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (92 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/sms` | Telnyx webhook handler |
| `GET` | `/listings` | Listings |
| `GET` | `/conversations` | Conversations |
| `GET` | `/flagged` | Flagged |
| `GET` | `/health` | Health check |

### Key Functions

- **`send_sms()`** — send sms
- **`ai_moderate()`** — ai moderate
- **`handle_sms()`** — handle sms
- **`list_listings()`** — list listings
- **`list_conversations()`** — list conversations
- **`list_flagged()`** — list flagged
- **`health()`** — health

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

Expose your local server for Telnyx webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and configure it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Webhook → `https://<id>.ngrok.io/webhooks/sms`

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X GET http://localhost:5000/listings \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or send an SMS to your Telnyx number to trigger the messaging workflow.

## Production Deployment

### Docker

```bash
docker build -t marketplace-comms-bridge-python .
docker run --env-file .env -p 5000:5000 marketplace-comms-bridge-python
```

### Makefile

```bash
make setup    # Install dependencies
make run      # Start the server
make docker   # Build and run in Docker
```

## Customize & Extend

- Replace in-memory storage with PostgreSQL or Redis for production
- Add authentication to your API endpoints
- Set up monitoring and alerting
- Extend Slack integration with richer workflows
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Messaging Guide](https://developers.telnyx.com/docs/messaging)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
