# Edge Compute Webhook Proxy

local dev server for testing webhook routing logic before deploying to Telnyx Edge. Includes the Edge function source and deployment instructions.

## Telnyx Products Used

- Speech Recognition / DTMF

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
                                          │
                                          ▼
                                  Customer Notification
                                      (SMS/Voice)
```

## Quick Start

### Prerequisites

- Python 3.8+
- A [Telnyx account](https://portal.telnyx.com/sign-up) with API key

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
docker build -t edge-compute-webhook-proxy .
docker run --env-file .env -p 5000:5000 edge-compute-webhook-proxy
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `VOICE_HANDLER_URL` | Service URL | Yes |
| `MESSAGE_HANDLER_URL` | Service URL | Yes |
| `DEFAULT_HANDLER_URL` | Service URL | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/edge-source` | `GET` /edge-source |
| `GET` | `/routes` | List all routes |
| `GET` | `/stats` | Dashboard / analytics view |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/edge-source
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
