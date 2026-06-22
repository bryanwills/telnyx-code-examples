# Build a Wireless Fleet Activation Portal — bulk activate SIMs with status tracking

Wireless Fleet Activation Portal — bulk activate SIMs with status tracking.

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

- **SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/wireless-fleet-activation-portal-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (61 lines). Here's what each piece does.

### Business Logic

- **`list_sims()`** — Makes an API call and processes the response.
- **`activate_sims()`** — Processes activate sims request and returns result.
- **`deactivate_sims()`** — Processes deactivate sims request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/sims` | List Sims |
| `POST` | `/sims/activate` | Activate Sims |
| `POST` | `/sims/deactivate` | Deactivate Sims |
| `GET` | `/activation-log` | Get Log |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def activate_sims():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    sim_ids = data.get("sim_ids", [])
    results = []
    for sim_id in sim_ids:
        try:
            resp = requests.patch(f"https://api.telnyx.com/v2/sim_cards/{sim_id}", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                json={"status": "active"}, timeout=10)
            status = "activated" if resp.ok else "failed"
            results.append({"sim_id": sim_id, "status": status})
```

The main endpoint processes the request:

```python
def list_sims():
    try:
        resp = requests.get("https://api.telnyx.com/v2/sim_cards", headers={"Authorization": f"Bearer {TELNYX_API_KEY}"},
            params={"page[size]": 50}, timeout=15)
        if resp.ok:
            return jsonify(resp.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Failed"}), 500

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
curl -X POST http://localhost:5000/sims/activate \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": ["+12125551234"],
    "carrier": "Current Carrier"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/sims | python3 -m json.tool
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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/wireless-fleet-activation-portal-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
