# Production-ready Flask application for eSIM provisioning via Telnyx.

> Application. Built with Telnyx IoT/SIM, Migration, Number Porting.

## What You'll Build

A production-ready **production-ready flask application for esim provisioning via telnyx** built with Python, Flask, and IoT/SIM, Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 221 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | IoT/SIM, Migration, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Create SIM Card (eSIM)**: `POST /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/create-sim-card)
- **Retrieve SIM Card**: `GET /v2/sim_cards/{id}` — [API reference](https://developers.telnyx.com/api/sim-cards/get-sim-card)
- **List SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)

## Webhook Events Handled

This app handles these webhook events:
- `sim_card.status.changed` -- SIM card status changed (active, suspended, deactivated)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/provision-esim-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (221 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/esim/profiles` | Profiles |
| `POST` | `/esim/profiles/<sim_card_id>/activate` | Activate |
| `GET` | `/esim/profiles/<sim_card_id>` | <Sim Card Id> |
| `GET` | `/esim/profiles` | Profiles |
| `POST` | `/esim/webhooks/sim-status` | Telnyx webhook handler |
| `GET` | `/health` | Health check |

### Key Functions

- **`create_app()`** — create app
- **`create_esim_profile()`** — create esim profile
- **`activate_esim_profile()`** — activate esim profile
- **`get_esim_profile()`** — get esim profile
- **`list_esim_profiles()`** — list esim profiles
- **`provision_esim()`** — provision esim
- **`activate_esim()`** — activate esim
- **`get_esim()`** — get esim
- **`list_esims()`** — list esims
- **`handle_sim_status_webhook()`** — handle sim status webhook

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

Expose your local server for Telnyx webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and configure it in the [Telnyx Portal](https://portal.telnyx.com):


## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/esim/profiles \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t provision-esim-python .
docker run --env-file .env -p 5000:5000 provision-esim-python
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
