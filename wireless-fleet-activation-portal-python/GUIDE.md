# Wireless Fleet Activation Portal — bulk activate SIMs with status tracking.

> Application. Built with Telnyx IoT/SIM, Migration, Number Porting.

## What You'll Build

A production-ready **wireless fleet activation portal — bulk activate sims with status tracking** built with Python, Flask, and IoT/SIM, Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 61 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | IoT/SIM, Migration, Number Porting |

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
cd telnyx-code-examples/wireless-fleet-activation-portal-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (61 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/sims` | Sims |
| `POST` | `/sims/activate` | Activate |
| `POST` | `/sims/deactivate` | Deactivate |
| `GET` | `/activation-log` | Activation Log |
| `GET` | `/health` | Health check |

### Key Functions

- **`list_sims()`** — list sims
- **`activate_sims()`** — activate sims
- **`deactivate_sims()`** — deactivate sims
- **`get_log()`** — get log
- **`health()`** — health

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
curl -X GET http://localhost:5000/sims \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t wireless-fleet-activation-portal-python .
docker run --env-file .env -p 5000:5000 wireless-fleet-activation-portal-python
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
