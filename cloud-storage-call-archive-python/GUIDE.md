# Cloud Storage Call Archive

> Cloud Storage Call Archive — archive call recordings to Telnyx Cloud Storage with searchable metadata.

## What You'll Build

A production-ready **cloud storage call archive** built with Python, Flask, and Cloud Storage, Migration, Number Porting, Voice.

| | |
|---|---|
| **Lines of code** | 91 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Cloud Storage, Migration, Number Porting, Voice |

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
- `call.recording.saved` — Call recording saved — URL available for download/processing

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/cloud-storage-call-archive-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (91 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/buckets` | Buckets |
| `GET` | `/buckets` | Buckets |
| `POST` | `/archive` | Archive |
| `POST` | `/webhooks/recording` | Telnyx webhook handler |
| `GET` | `/archive` | Archive |
| `GET` | `/archive/search` | Search |
| `GET` | `/health` | Health check |

### Key Functions

- **`create_bucket()`** — create bucket
- **`list_buckets()`** — list buckets
- **`archive_recording()`** — archive recording
- **`handle_recording_webhook()`** — handle recording webhook
- **`list_archive()`** — list archive
- **`search_archive()`** — search archive
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
curl -X POST http://localhost:5000/buckets \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t cloud-storage-call-archive-python .
docker run --env-file .env -p 5000:5000 cloud-storage-call-archive-python
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
