# Cloud Storage Media CDN

> Cloud Storage Media CDN — use Telnyx Cloud Storage as a CDN for IVR prompts, hold music, and voice assets.

## What You'll Build

A production-ready **cloud storage media cdn** built with Python, Flask, and Cloud Storage, Migration, Number Porting, Voice.

| | |
|---|---|
| **Lines of code** | 84 |
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

- **Upload Object**: `PUT https://storage.telnyx.com/{bucket}/{key}` — [Cloud Storage docs](https://developers.telnyx.com/docs/cloud-storage)
- **Download Object**: `GET https://storage.telnyx.com/{bucket}/{key}` — [Cloud Storage docs](https://developers.telnyx.com/docs/cloud-storage)
- **List Objects**: `GET /v2/storage/buckets/{bucket}/objects` — [API reference](https://developers.telnyx.com/api/cloud-storage/list-objects)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/cloud-storage-media-cdn-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (84 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/setup` | Setup |
| `POST` | `/upload` | Upload |
| `GET` | `/media` | Media |
| `GET` | `/media/<category>/<name>` | <Name> |
| `GET` | `/ivr-config` | Ivr Config |
| `GET` | `/health` | Health check |

### Key Functions

- **`setup_bucket()`** — setup bucket
- **`upload_media()`** — upload media
- **`list_media()`** — list media
- **`get_media_url()`** — get media url
- **`ivr_config()`** — ivr config
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
curl -X POST http://localhost:5000/setup \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t cloud-storage-media-cdn-python .
docker run --env-file .env -p 5000:5000 cloud-storage-media-cdn-python
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
