# Policy Renewal Campaign

> Automated multi-channel renewal reminders. 60 days: SMS. 30 days: AI voice call reviewing coverage changes. 7 days: urgent SMS. Agent reviews lapsed policies for win-back.

## What You'll Build

A production-ready **policy renewal campaign** built with Python, Flask, and Voice, AI Inference.

Integrates with Stripe, Slack for extended functionality.

| | |
|---|---|
| **Lines of code** | 123 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Voice, AI Inference |
| **Channels** | voice, sms |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [Slack webhook URL](https://api.slack.com/messaging/webhooks)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Call Control: Gather (STT/DTMF)**: `POST /v2/calls/{id}/actions/gather_using_speak` — [API reference](https://developers.telnyx.com/api/call-control/gather)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` — [API reference](https://developers.telnyx.com/api/call-control/speak)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Webhook Events Handled

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.answered` — Call connected — app begins interaction
- `call.gather.ended` — Caller input received (speech transcription or DTMF digits)
- `call.speak.ended` — TTS playback finished — app transitions to next action (gather, transfer, etc.)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/policy-renewal-campaign-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (123 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/campaigns/run` | Run |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `POST` | `/webhooks/sms` | Telnyx webhook handler |
| `GET` | `/policies` | Policies |
| `GET` | `/campaign-log` | Campaign Log |
| `GET` | `/health` | Health check |

### Key Functions

- **`send_sms()`** — send sms
- **`run_campaign()`** — run campaign
- **`handle_voice()`** — handle voice
- **`handle_sms()`** — handle sms
- **`list_policies()`** — list policies
- **`get_log()`** — get log
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
curl -X POST http://localhost:5000/campaigns/run \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

Or send an SMS to your Telnyx number to trigger the messaging workflow.

## Production Deployment

### Docker

```bash
docker build -t policy-renewal-campaign-python .
docker run --env-file .env -p 5000:5000 policy-renewal-campaign-python
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
- Extend Stripe, Slack integration with richer workflows
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
