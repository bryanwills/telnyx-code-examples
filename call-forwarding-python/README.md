# Call Forwarding

Production-ready Flask application for call forwarding via Telnyx Voice API.

## Telnyx Products Used

- Voice Call Control

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
docker build -t call-forwarding .
docker run --env-file .env -p 5000:5000 call-forwarding
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `FORWARD_TO_NUMBER` | Phone number in E.164 format | Yes |
| `FLASK_DEBUG` | Flask Debug | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/call` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/calls/status/<call_control_id>` | List all call status |
| `POST` | `/calls/hangup/<call_control_id>` | `POST` /calls/hangup/<call_control_id> |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/calls/status/<call_control_id>
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/calls/hangup/<call_control_id> \
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
