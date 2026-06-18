# Porting Order Tracker Dashboard

Porting Order Tracker Dashboard â submit, track, and manage porting orders with SLA monitoring, timeline visualization, and bulk operations.

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
docker build -t porting-order-tracker-dashboard .
docker run --env-file .env -p 5000:5000 porting-order-tracker-dashboard
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `ALERT_WEBHOOK` | Webhook URL for external notifications | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/porting` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/porting/orders` | `POST` /porting/orders |
| `POST` | `/porting/bulk` | `POST` /porting/bulk |
| `GET` | `/porting/orders` | List all orders |
| `GET` | `/porting/sla-check` | `GET` /porting/sla-check |
| `GET` | `/porting/dashboard` | Dashboard / analytics view |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/porting/orders
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/porting/orders \
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
