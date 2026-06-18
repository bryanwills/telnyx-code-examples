# Inbound Sip Routing

Flask application for managing inbound SIP routing with Telnyx.

## Telnyx Products Used

- MMS Media Handling

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
docker build -t inbound-sip-routing .
docker run --env-file .env -p 5000:5000 inbound-sip-routing
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `FLASK_DEBUG` | Flask Debug | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sip/connections` | List all connections |
| `POST` | `/sip/connections` | Create new record |
| `GET` | `/sip/connections/<connection_id>` | List all connection |

## Testing

**List records:**

```bash
curl http://localhost:5000/sip/connections
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/sip/connections \
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
