# Production-ready Flask application for SIM card activation via Telnyx.

> Application. Built with Telnyx IoT/SIM, Migration, Number Porting.

## What You'll Build

A production-ready **production-ready flask application for sim card activation via telnyx** built with Python, Flask, and IoT/SIM, Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 117 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | IoT/SIM, Migration, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **List SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)
- **Retrieve SIM Card**: `GET /v2/sim_cards/{id}` — [API reference](https://developers.telnyx.com/api/sim-cards/get-sim-card)
- **Activate SIM Card**: `PATCH /v2/sim_cards/{id}` — [API reference](https://developers.telnyx.com/api/sim-cards/update-sim-card)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/activate-sim-card-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (117 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/sim-cards` | Sim Cards |
| `GET` | `/sim-cards/<sim_card_id>` | <Sim Card Id> |
| `POST` | `/sim-cards/<sim_card_id>/activate` | Activate |

### Key Functions

- **`list_sim_cards()`** — list sim cards
- **`get_sim_card()`** — get sim card
- **`activate_sim_card()`** — activate sim card
- **`list_sims()`** — list sims
- **`get_sim()`** — get sim
- **`activate_sim()`** — activate sim

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
curl -X GET http://localhost:5000/sim-cards \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t activate-sim-card-python .
docker run --env-file .env -p 5000:5000 activate-sim-card-python
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
