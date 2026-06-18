# Track Iot Device Location

Production-ready Flask application for device location tracking via Telnyx IoT API.

## Telnyx Products Used

- Verify API

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
docker build -t track-iot-device-location .
docker run --env-file .env -p 5000:5000 track-iot-device-location
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `FLASK_DEBUG` | Flask Debug | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/devices` | List all devices |
| `GET` | `/devices/<sim_card_id>` | List all device location |
| `GET` | `/devices/<sim_card_id>/location` | List all location only |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/devices
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
