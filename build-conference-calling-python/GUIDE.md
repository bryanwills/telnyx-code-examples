# Production-ready Flask application for managing conference calls via Telnyx.

> Application. Built with Telnyx Migration, Number Porting, Voice.

## What You'll Build

A production-ready **production-ready flask application for managing conference calls via telnyx** built with Python, Flask, and Migration, Number Porting, Voice.

| | |
|---|---|
| **Lines of code** | 298 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Number Porting, Voice |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)

## Webhook Events Handled

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.answered` — Call connected — app begins interaction
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/build-conference-calling-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (298 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/conference/create` | Create |
| `POST` | `/conference/<conference_name>/add-participant` | Add Participant |
| `POST` | `/conference/<conference_name>/end` | End |
| `GET` | `/conference/<conference_name>/status` | Status |
| `POST` | `/webhooks/call-events` | Telnyx webhook handler |
| `GET` | `/health` | Health check |

### Key Functions

- **`create_conference()`** — create conference
- **`add_participant_to_conference()`** — add participant to conference
- **`end_conference()`** — end conference
- **`get_conference_status()`** — get conference status
- **`create_conference_endpoint()`** — create conference endpoint
- **`add_participant_endpoint()`** — add participant endpoint
- **`end_conference_endpoint()`** — end conference endpoint
- **`get_conference_status_endpoint()`** — get conference status endpoint
- **`handle_call_webhook()`** — handle call webhook
- **`health_check()`** — health check

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
docker build -t build-conference-calling-python .
docker run --env-file .env -p 5000:5000 build-conference-calling-python
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
