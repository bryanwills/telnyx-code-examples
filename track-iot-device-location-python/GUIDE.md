# Build a Production-ready Flask application for device location

Production-ready Flask application for device location tracking via Telnyx IoT API.

## How It Works

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Telnyx IoT API    │
  │ • Query SIM       │
  │ • Get cell tower  │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Location Mapping  │
  │ • Lat/long        │
  │ • Geofence check  │
  └────────┬─────────┘
           │
           ▼
  JSON response
  (location + alerts)
```

## Telnyx Products Used

- **IoT/SIM** — cellular connectivity and device management
- **Migration**
- **Number Porting** — phone number search, purchase, and configuration
- **Verify** — phone verification with OTP delivery across channels

## API Endpoints

- **SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/track-iot-device-location-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (202 lines). Here's what each piece does.

### Business Logic

- **`list_devices()`** — Returns all devices with metadata and pagination.
- **`get_device_location()`** — Fetches device location by ID with full details.
- **`get_location_only()`** — Fetches location only by ID with full details.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/devices` | List Devices |
| `GET` | `/devices/<sim_card_id>` | Get Device Location |
| `GET` | `/devices/<sim_card_id>/location` | Get Location Only |
| `GET` | `/health` | Health check |

The main endpoint processes the request:

```python
def list_devices():
    """List all SIM cards (devices) in the account."""
    try:
        devices = list_all_sim_cards()
        return jsonify({"devices": devices}), 200
        
    except telnyx.AuthenticationError:
        return jsonify({"error": "Invalid API key"}), 401
    except telnyx.RateLimitError:
        return jsonify({"error": "Rate limit exceeded"}), 429
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Check results:**

```bash
curl http://localhost:5000/devices | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/track-iot-device-location-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
