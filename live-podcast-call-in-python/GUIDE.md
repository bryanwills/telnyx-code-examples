# Live Podcast Call-In Show

> Hosts on a conference call, listeners call in. AI screens callers via STT, queues approved ones, generates real-time fact-checks for the host, TTS announces topics.

## What You'll Build

A production-ready **live podcast call-in show** built with Python, Flask, and Voice, AI Inference, Conferencing, Media Streaming.

Integrates with Slack for extended functionality.

| | |
|---|---|
| **Lines of code** | 314 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Voice, AI Inference, Conferencing, Media Streaming |
| **Channels** | voice, api |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [Slack webhook URL](https://api.slack.com/messaging/webhooks)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Create Call**: `POST /v2/calls` -- [ref](https://developers.telnyx.com/api/call-control/create-call)
- **Answer**: `POST /v2/calls/{id}/actions/answer` -- [ref](https://developers.telnyx.com/api/call-control/answer-call)
- **Gather (screen)**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [ref](https://developers.telnyx.com/api/call-control/gather)
- **Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [ref](https://developers.telnyx.com/api/call-control/speak)
- **Join Conference**: `POST /v2/calls/{id}/actions/join_conference` -- [ref](https://developers.telnyx.com/api/call-control/join-conference)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [ref](https://developers.telnyx.com/api/inference/chat-completions)

## Webhook Events Handled

- `call.initiated` -- New inbound caller
- `call.answered` -- Caller connected, begin screening
- `call.gather.ended` -- Caller stated topic, AI evaluates
- `call.hangup` -- Caller disconnected

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/live-podcast-call-in-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (314 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/shows/start` | Start |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `POST` | `/shows/<show_id>/next-caller` | Next Caller |
| `POST` | `/shows/<show_id>/fact-check` | Fact Check |
| `GET` | `/shows/<show_id>/queue` | Queue |
| `GET` | `/shows` | Shows |
| `GET` | `/health` | Health check |

### Key Functions

- **`telnyx_post()`** — telnyx post
- **`inference()`** — inference
- **`notify_slack()`** — notify slack
- **`start_show()`** — start show
- **`handle_voice()`** — handle voice
- **`admit_next_caller()`** — admit next caller
- **`fact_check()`** — fact check
- **`view_queue()`** — view queue
- **`list_shows()`** — list shows
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
curl -X POST http://localhost:5000/shows/start \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t live-podcast-call-in-python .
docker run --env-file .env -p 5000:5000 live-podcast-call-in-python
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
