# Number Porting Status Tracker

Number Porting Status Tracker — track porting orders with status webhooks and SMS alerts.

## Telnyx Products Used

- SMS/MMS Messaging

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
docker build -t number-porting-status-tracker .
docker run --env-file .env -p 5000:5000 number-porting-status-tracker
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `ALERT_NUMBER` | Phone number in E.164 format | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/porting` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/ports/list` | List all ports |
| `POST` | `/ports/create` | Create new record |
| `GET` | `/ports/<order_id>` | List all port |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/ports/list
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/ports/create \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [SMS & MMS Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
