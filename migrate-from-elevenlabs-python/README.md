# Migrate From Elevenlabs

Migrate from ElevenLabs — import ElevenLabs voice configurations to Telnyx TTS with voice mapping and cost comparison.

## How It Works

1. Customer **calls** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (call)                                     │
                                          │
                                          ▼
                                  Customer Notification
                                      (SMS/Voice)
```

## Quick Start

### Prerequisites

- Python 3.8+
- A [Telnyx account](https://portal.telnyx.com/sign-up) with API key
- A Telnyx phone number with voice and/or messaging enabled
- A [Call Control Application](https://portal.telnyx.com/app#/call-control/applications) configured with your webhook URL

### Install & Run

```bash
# Configure
cp .env.example .env
# Edit .env with your real credentials

# Install
pip install -r requirements.txt

# Run
python app.py
```

### Docker

```bash
docker build -t migrate-from-elevenlabs .
docker run --env-file .env -p 5000:5000 migrate-from-elevenlabs
```

### Expose Your Webhook

For local development, use [ngrok](https://ngrok.com) to expose your server:

```bash
ngrok http 5000
```

Then set your Telnyx webhook URL to the ngrok HTTPS URL:

- **Voice:** `https://<your-ngrok>.ngrok.io/webhooks/voice`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `ELEVENLABS_API_KEY` | API key | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/audit/elevenlabs` | `GET` /audit/elevenlabs |
| `POST` | `/migrate/voice-config` | `POST` /migrate/voice-config |
| `GET` | `/mapping/voices` | `GET` /mapping/voices |
| `GET` | `/cost-comparison` | `GET` /cost-comparison |
| `POST` | `/test-tts` | `POST` /test-tts |
| `GET` | `/migration-log` | List all log |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/audit/elevenlabs
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/migrate/voice-config \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
