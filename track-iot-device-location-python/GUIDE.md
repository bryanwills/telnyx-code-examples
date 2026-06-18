# Production-ready Flask application for device location

> Production-ready Flask application for device location tracking via Telnyx IoT API.

## What You'll Build

A production-ready **production-ready flask application for device location** built with Python, Flask, and IoT/SIM, Migration, Number Porting, Verify.

| | |
|---|---|
| **Lines of code** | 202 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | IoT/SIM, Migration, Number Porting, Verify |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/track-iot-device-location-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (202 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/devices` | Devices |
| `GET` | `/devices/<sim_card_id>` | <Sim Card Id> |
| `GET` | `/devices/<sim_card_id>/location` | Location |
| `GET` | `/health` | Health check |

### Key Functions

- **`get_sim_card_details()`** — get sim card details
- **`get_sim_network_usage()`** — get sim network usage
- **`list_all_sim_cards()`** — list all sim cards
- **`list_devices()`** — list devices
- **`get_device_location()`** — get device location
- **`get_location_only()`** — get location only
- **`health_check()`** — health check

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X GET http://localhost:5000/devices \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t track-iot-device-location-python .
docker run --env-file .env -p 5000:5000 track-iot-device-location-python
```

### Makefile

```bash
make setup    # Install dependencies
make run      # Start the server
make docker   # Build and run in Docker
```

## Customize & Extend

- Replace in-memory storage with PostgreSQL or Redis for production
- Add authentication to your API endpoints
- Set up monitoring and alerting
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
