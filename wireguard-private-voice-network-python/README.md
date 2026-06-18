# Wireguard Private Voice Network

WireGuard Private Voice Network — create WireGuard mesh network for private SIP trunking with encrypted voice traffic.

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
docker build -t wireguard-private-voice-network .
docker run --env-file .env -p 5000:5000 wireguard-private-voice-network
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/networks` | Create new record |
| `GET` | `/networks` | List all networks |
| `POST` | `/interfaces` | Create new record |
| `POST` | `/peers` | Create new record |
| `GET` | `/interfaces/<iface_id>/config` | List all config |
| `GET` | `/topology` | `GET` /topology |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/networks
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/networks \
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
