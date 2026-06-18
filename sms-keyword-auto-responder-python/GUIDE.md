# SMS Keyword Auto-Responder — keyword-triggered responses with match analytics.

> SMS application. Built with Telnyx Migration, Number Porting, SMS/MMS.

## What You'll Build

A production-ready **sms keyword auto-responder — keyword-triggered responses with match analytics** built with Python, Flask, and SMS/MMS.

| | |
|---|---|
| **Lines of code** | 71 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | SMS/MMS |
| **Channels** | sms |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Send Message**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Webhook Events Handled

This app handles these webhook events ([Messaging docs](https://developers.telnyx.com/docs/api/v2/messaging)):
- `message.received` — Inbound SMS/MMS received

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/sms-keyword-auto-responder-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (71 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/messaging` | Telnyx webhook handler |
| `GET` | `/keywords` | Keywords |
| `POST` | `/keywords` | Keywords |
| `GET` | `/analytics` | Analytics |
| `GET` | `/health` | Health check |

### Key Functions

- **`send_sms()`** — send sms
- **`handle_sms()`** — handle sms
- **`list_keywords()`** — list keywords
- **`add_keyword()`** — add keyword
- **`analytics()`** — analytics
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
curl -X GET http://localhost:5000/keywords \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or send an SMS to your Telnyx number to trigger the messaging workflow.

## Production Deployment

### Docker

```bash
docker build -t sms-keyword-auto-responder-python .
docker run --env-file .env -p 5000:5000 sms-keyword-auto-responder-python
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
- [Messaging Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
