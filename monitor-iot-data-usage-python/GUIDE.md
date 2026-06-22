# Build a Production-ready Flask application for monitoring SIM card

Production-ready Flask application for monitoring SIM card data usage via Telnyx IoT API.

## How It Works

```
  ┌──────────────────┐
  │ IoT Device Event │
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

- **SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)

## Webhook Events

Your app receives webhook events from Telnyx as things happen.

This app handles these webhook events:
- `sim_card.data_limit.reached` — SIM card data usage limit reached
- `sim_card.status.changed` — SIM card status changed (active, suspended, etc.)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/monitor-iot-data-usage-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (234 lines). Here's what each piece does.

### Handling Webhooks

Webhook handlers process events from Telnyx:

**`handle_sim_webhook()`** — Handles Telnyx webhook events. Routes each event type to the appropriate handler.

### Business Logic

- **`health_check()`** — Health check endpoint for monitoring and load balancer probes.
- **`list_sims()`** — Queries Telnyx IoT API for SIM cards.
- **`get_sim()`** — Queries Telnyx IoT API for SIM cards.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check |
| `GET` | `/sim-cards` | List Sims |
| `GET` | `/sim-cards/<sim_card_id>` | Get Sim |
| `GET` | `/sim-cards/<sim_card_id>/usage` | Get Usage |
| `GET` | `/sim-cards/<sim_card_id>/health` | Health check |
| `POST` | `/sim-cards/<sim_card_id>/activate` | Activate Sim |
| `POST` | `/webhooks/sim-events` | Telnyx webhook handler |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    # Handle specific event types
    if event_type == "sim_card.status.changed":
        sim_id = event_data.get("id")
        new_status = event_data.get("status")
        print(f"SIM {sim_id} status changed to {new_status}")
        
    elif event_type == "sim_card.data_limit.reached":
        sim_id = event_data.get("id")
        print(f"ALERT: SIM {sim_id} has reached its data limit")
    
    # Always return 200 to acknowledge receipt
    return jsonify({"status": "received"}), 200

```

The trigger endpoint kicks off the workflow:

```python
def activate_sim(sim_card_id: str):
    """Activate a SIM card."""
    try:
        response = client.sim_cards.activate(sim_card_id)
        
        return jsonify({
            "id": response.data.id,
            "status": response.data.status,
            "message": "SIM card activated successfully",
        }), 200
        
    except telnyx.AuthenticationError:
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

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/monitor-iot-data-usage-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
