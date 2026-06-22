# Build a Porting Order Tracker Dashboard

Track number porting requests in real time. Your app receives Telnyx porting webhooks, stores order status, and exposes a dashboard API showing which numbers have ported, which are pending, and which failed.

## How It Works

```
  Porting Webhook
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx Number Porting
           │
           ├──► A/B testing
           │
           ▼
     JSON response
```

## API Endpoints

- **List Porting Orders**: `GET /v2/porting_orders` — [API reference](https://developers.telnyx.com/api/porting/list-porting-orders)
- **Retrieve Porting Order**: `GET /v2/porting_orders/{id}` — [API reference](https://developers.telnyx.com/api/porting/get-porting-order)

## Webhook Events

Your app receives webhook events from Telnyx as things happen.

This app handles these webhook events:
- `porting_order.status_changed` -- Porting order status updated (FOC date set, completed, rejected)
- `number_order.complete` -- Phone number order completed and ready to use

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/porting-order-tracker-dashboard-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (120 lines). Here's what each piece does.

### Handling Webhooks

Webhook handlers process events from Telnyx:

**`handle_webhook()`** — Handles Telnyx webhook events. Routes each event type to the appropriate handler.

### Business Logic

- **`check_sla_breach()`** — Processes check sla breach request and returns result.
- **`submit_order()`** — Makes an API call and processes the response.
- **`bulk_submit()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/porting/orders` | Submit Order |
| `POST` | `/porting/bulk` | Bulk Submit |
| `POST` | `/porting/orders` | List Orders |
| `POST` | `/webhooks/porting` | Telnyx webhook handler |
| `GET` | `/porting/sla-check` | Sla Check |
| `GET` | `/porting/dashboard` | Dashboard |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def submit_order():
    data = request.get_json()
    try:
        resp = requests.post(f"{API}/porting_orders", headers=headers,
            json={"phone_numbers": data.get("phone_numbers", [], timeout=10),
                "authorized_person": data.get("authorized_person"),
                "current_provider": data.get("current_provider"),
                "billing_phone_number": data.get("billing_phone_number"),
                "customer_reference": data.get("reference", "")}, timeout=15)
        result = resp.json()
        order = {"id": result.get("data", {}).get("id"), "numbers": data.get("phone_numbers"),
            "count": len(data.get("phone_numbers", [])), "provider": data.get("current_provider"),
```

The main endpoint processes the request:

```python
def submit_order():
    data = request.get_json()
    try:
        resp = requests.post(f"{API}/porting_orders", headers=headers,
            json={"phone_numbers": data.get("phone_numbers", [], timeout=10),
                "authorized_person": data.get("authorized_person"),
                "current_provider": data.get("current_provider"),
                "billing_phone_number": data.get("billing_phone_number"),
                "customer_reference": data.get("reference", "")}, timeout=15)
        result = resp.json()
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
curl -X POST http://localhost:5000/porting/orders \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999",
    "order_id": "ORD-12345",
    "items": ["Widget Pro"],
    "total": 99.99
  }'
```

**Check results:**

```bash
curl http://localhost:5000/porting/sla-check | python3 -m json.tool
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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/porting-order-tracker-dashboard-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
