# Activate Sim Card

Production-ready Flask application for SIM card activation via Telnyx.

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
docker build -t activate-sim-card .
docker run --env-file .env -p 5000:5000 activate-sim-card
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `FLASK_DEBUG` | Flask Debug | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sim-cards` | List all sims |
| `GET` | `/sim-cards/<sim_card_id>` | List all sim |
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
