# Media Stream Voice Cloak

Media Stream Voice Cloak — real-time voice modification via media streaming API. Apply pitch shift, echo, or anonymization.

## Telnyx Products Used

- MMS Media Handling
- Voice Call Control

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
docker build -t media-stream-voice-cloak .
docker run --env-file .env -p 5000:5000 media-stream-voice-cloak
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
| `STREAM_WEBSOCKET_URL` | Service URL | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/cloak/<ccid>` | `POST` /cloak/<ccid> |
| `GET` | `/effects` | List all effects |
| `GET` | `/active` | List all active |
| `GET` | `/log` | List all log |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/effects
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/cloak/<ccid> \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
