# Conference Live Poll via DTMF

> Conference Live Poll via DTMF — host asks a question, all conference participants vote by pressing 1-4, results tallied instantly.

## What You'll Build

A production-ready **conference live poll via dtmf** built with Python, Flask, and Voice.

| | |
|---|---|
| **Lines of code** | 108 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Voice |
| **Channels** | voice |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Webhook Events Handled

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.answered` — Call connected — app begins interaction
- `call.gather.ended` — Caller input received (speech transcription or DTMF digits)
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.speak.ended` — TTS playback finished — app transitions to next action (gather, transfer, etc.)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/conference-live-poll-dtmf-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (108 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/conference/create` | Create |
| `POST` | `/conference/<cid>/invite` | Invite |
| `POST` | `/conference/<cid>/poll` | Poll |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/conference/<cid>/results` | Results |
| `GET` | `/health` | Health check |

### Key Functions

- **`create_conference()`** — create conference
- **`invite()`** — invite
- **`start_poll()`** — start poll
- **`handle_voice()`** — handle voice
- **`poll_results()`** — poll results
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
curl -X POST http://localhost:5000/conference/create \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t conference-live-poll-dtmf-python .
docker run --env-file .env -p 5000:5000 conference-live-poll-dtmf-python
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
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
