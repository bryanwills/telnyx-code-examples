# TeXML Voicemail Drop — leave pre-recorded voicemails at scale via TeXML.

> Voice application. Built with Telnyx Migration, Number Porting, Voice.

## What You'll Build

A production-ready **texml voicemail drop — leave pre-recorded voicemails at scale via texml** built with Python, Flask, and Voice.

| | |
|---|---|
| **Lines of code** | 73 |
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

- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` — [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **Call Control: Start Playback**: `POST /v2/calls/{id}/actions/playback_start` — [API reference](https://developers.telnyx.com/api/call-control/start-playback)
- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Webhook Events Handled

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.machine.detection.ended` — Answering machine detection completed — human or machine result
- `call.playback.ended` — Audio file playback completed

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/texml-voicemail-drop-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (73 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/drop` | Drop |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/drops` | Drops |
| `GET` | `/health` | Health check |

### Key Functions

- **`voicemail_drop()`** — voicemail drop
- **`handle_voice()`** — handle voice
- **`list_drops()`** — list drops
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
curl -X POST http://localhost:5000/drop \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t texml-voicemail-drop-python .
docker run --env-file .env -p 5000:5000 texml-voicemail-drop-python
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
