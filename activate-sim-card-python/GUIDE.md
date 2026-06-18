# Build a Production-ready Flask application for SIM card activation via Telnyx

Application. Built with Telnyx IoT/SIM, Migration, Number Porting.

## How It Works

```
  ┌──────────────────┐
  │ API Request      │
  │ (SIM data /       │
  │  sensor reading)   │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Threshold Check   │
  └────────┬─────────┘
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **IoT/SIM** — cellular connectivity and device management
- **Migration**
- **Number Porting** — phone number search, purchase, and configuration

## API Endpoints

- **List SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)
- **Retrieve SIM Card**: `GET /v2/sim_cards/{id}` — [API reference](https://developers.telnyx.com/api/sim-cards/get-sim-card)
- **Activate SIM Card**: `PATCH /v2/sim_cards/{id}` — [API reference](https://developers.telnyx.com/api/sim-cards/update-sim-card)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/activate-sim-card-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (117 lines). Here's what each piece does.

### Business Logic

- **`list_sims()`** — Queries Telnyx IoT API for SIM cards.
- **`get_sim()`** — Queries Telnyx IoT API for SIM cards.
- **`activate_sim()`** — Fetches SIM card details including data usage.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/sim-cards` | List Sims |
| `GET` | `/sim-cards/<sim_card_id>` | Get Sim |
| `POST` | `/sim-cards/<sim_card_id>/activate` | Activate Sim |


The trigger endpoint kicks off the workflow:

```python
def activate_sim(sim_card_id):
    """HTTP endpoint to activate a SIM card."""
    try:
        result = activate_sim_card(sim_card_id)
        return jsonify({"message": "SIM card activated successfully", "data": result}), 200
        
    except telnyx.AuthenticationError:
        return jsonify({"error": "Invalid API key"}), 401
    except telnyx.RateLimitError:
        return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429
    except telnyx.APIStatusError as e:
        return jsonify({"error": "API request failed", "status_code": e.status_code}), e.status_code
```

The main endpoint processes the request:

```python
def list_sims():
    """HTTP endpoint to list all SIM cards."""
    try:
        sims = list_sim_cards()
        return jsonify({"data": sims}), 200
        
    except telnyx.AuthenticationError:
        return jsonify({"error": "Invalid API key"}), 401
    except telnyx.RateLimitError:
        return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429
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

**Trigger the workflow:**

```bash
curl -X POST http://localhost:5000/sim-cards/<sim_card_id>/activate \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEV-001",
    "event": "threshold_exceeded",
    "value": 95.2
  }'
```

**Check results:**

```bash
curl http://localhost:5000/sim-cards | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Deploy

```bash
# Docker
docker build -t activate-sim-card-python .
docker run --env-file .env -p 5000:5000 activate-sim-card-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
