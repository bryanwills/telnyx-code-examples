# AI Sales Coach (Whisper)

> AI coach listens to a live sales call and whispers real-time suggestions to the rep only. Customer never hears the AI. Generates post-call scorecard.

## What You'll Build

A production-ready **ai sales coach (whisper)** built with Python, Flask, and Voice, AI Inference, Conferencing, Media Streaming.

Integrates with Slack for extended functionality.

| | |
|---|---|
| **Lines of code** | 238 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Voice, AI Inference, Conferencing, Media Streaming |
| **Channels** | voice |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [Slack webhook URL](https://api.slack.com/messaging/webhooks)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

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
cd telnyx-code-examples/ai-sales-coach-whisper-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (238 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sessions/start` | Start |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `POST` | `/webhooks/media` | Telnyx webhook handler |
| `GET` | `/sessions` | Sessions |
| `GET` | `/sessions/<name>` | <Name> |
| `GET` | `/health` | Health check |

### Key Functions

- **`telnyx_post()`** — telnyx post
- **`telnyx_call_action()`** — telnyx call action
- **`call_inference()`** — call inference
- **`start_coaching()`** — start coaching
- **`handle_voice()`** — handle voice
- **`handle_media()`** — handle media
- **`list_sessions()`** — list sessions
- **`get_session()`** — get session
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

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/sessions/start \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t ai-sales-coach-whisper-python .
docker run --env-file .env -p 5000:5000 ai-sales-coach-whisper-python
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
- Add conversation memory for multi-turn AI interactions
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
