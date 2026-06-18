# Billing Anomaly Detector

Billing Anomaly Detector — monitor usage and billing for anomalies, alert on cost spikes and unusual patterns.

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
docker build -t billing-anomaly-detector .
docker run --env-file .env -p 5000:5000 billing-anomaly-detector
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `ALERT_WEBHOOK` | Webhook URL for external notifications | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/config` | `POST` /config |
| `GET` | `/config` | List all baselines |
| `POST` | `/check` | Trigger workflow execution |
| `GET` | `/balance` | `GET` /balance |
| `GET` | `/alerts` | List all alerts |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/config
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/config \
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
