# Autonomous Outbound Sales Agent

> Autonomous Outbound Sales Agent — AI-driven lead qualification, objection handling, and meeting booking.

## What You'll Build

A production-ready **autonomous outbound sales agent** built with Python, Flask, and SMS/MMS, Voice, AI Inference, Number Lookup.

| | |
|---|---|
| **Lines of code** | 265 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | SMS/MMS, Voice, AI Inference, Number Lookup |
| **Channels** | voice |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)
- **Send Message**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Number Lookup**: `GET /v2/number_lookup/{phone}` — [API reference](https://developers.telnyx.com/api/number-lookup/lookup)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Webhook Events Handled

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.answered` — Call connected — app begins interaction
- `call.gather.ended` — Caller input received (speech transcription or DTMF digits)
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.speak.ended` — TTS playback finished — app transitions to next action (gather, transfer, etc.)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/autonomous-outbound-sales-agent-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (265 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/leads` | Leads |
| `POST` | `/campaign/start` | Start |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/results` | Results |
| `GET` | `/health` | Health check |

### Key Functions

- **`call_inference()`** — call inference
- **`lookup_number()`** — lookup number
- **`generate_disposition()`** — generate disposition
- **`send_confirmation_sms()`** — send confirmation sms
- **`add_leads()`** — add leads
- **`start_campaign()`** — start campaign
- **`handle_voice_webhook()`** — handle voice webhook
- **`get_results()`** — get results
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

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`
- **Messaging Profile** → Inbound Webhook → `https://<id>.ngrok.io/webhooks/sms`

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/leads \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

Or send an SMS to your Telnyx number to trigger the messaging workflow.

## Production Deployment

### Docker

```bash
docker build -t autonomous-outbound-sales-agent-python .
docker run --env-file .env -p 5000:5000 autonomous-outbound-sales-agent-python
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
- Add conversation memory for multi-turn AI interactions
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Messaging Guide](https://developers.telnyx.com/docs/messaging)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
