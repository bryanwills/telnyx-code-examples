# Monitor Iot Data Usage

Production-ready Flask application for monitoring SIM card data usage via Telnyx IoT API.

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
docker build -t monitor-iot-data-usage .
docker run --env-file .env -p 5000:5000 monitor-iot-data-usage
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `DATA_LIMIT_THRESHOLD_MB` | Threshold value | No |
| `FLASK_DEBUG` | Flask Debug | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/sim-events` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check and service status |
| `GET` | `/sim-cards` | List all sims |
| `GET` | `/sim-cards/<sim_card_id>` | List all sim |
| `GET` | `/sim-cards/<sim_card_id>/usage` | List all usage |
| `GET` | `/sim-cards/<sim_card_id>/health` | Health check and service status |
| `POST` | `/sim-cards/<sim_card_id>/activate` | `POST` /sim-cards/<sim_card_id>/activate |

## Testing

**List records:**

```bash
curl http://localhost:5000/sim-cards
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/sim-cards/<sim_card_id>/activate \
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
