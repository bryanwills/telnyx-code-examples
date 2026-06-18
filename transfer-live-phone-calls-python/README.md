# Transfer Live Phone Calls

Production-ready Flask application for call transfer via Telnyx Voice API.

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
docker build -t transfer-live-phone-calls .
docker run --env-file .env -p 5000:5000 transfer-live-phone-calls
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `TELNYX_PHONE_NUMBER` | Phone number in E.164 format | Yes |
| `TELNYX_CONNECTION_ID` | Telnyx Connection Id | Yes |
| `FLASK_DEBUG` | Flask Debug | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/call-events` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/calls/initiate` | `POST` /calls/initiate |
| `POST` | `/calls/transfer` | `POST` /calls/transfer |
| `POST` | `/calls/hangup` | `POST` /calls/hangup |
| `GET` | `/calls/status/<call_control_id>` | List all call status |

## Testing

**List records:**

```bash
curl http://localhost:5000/calls/status/<call_control_id>
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/calls/initiate \
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
