# Texml Dynamic Call Router

TeXML Dynamic Call Router — time-of-day and caller-based routing with TeXML responses.

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
docker build -t texml-dynamic-call-router .
docker run --env-file .env -p 5000:5000 texml-dynamic-call-router
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BUSINESS_HOURS_NUMBER` | Phone number in E.164 format | No |
| `AFTER_HOURS_NUMBER` | Phone number in E.164 format | No |
| `VOICEMAIL_URL` | Service URL | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/texml/route` | `POST` /texml/route |
| `POST` | `/texml/recording` | `POST` /texml/recording |
| `POST` | `/vip` | Create new record |
| `GET` | `/calls` | List all calls |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/calls
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/texml/route \
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
