# Porting Order Tracker Dashboard

> 

## What You'll Build

A production-ready **porting order tracker dashboard** built with Python, Flask, and Telnyx APIs.

| | |
|---|---|
| **Lines of code** | 120 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** |  |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **List Porting Orders**: `GET /v2/porting_orders` — [API reference](https://developers.telnyx.com/api/porting/list-porting-orders)
- **Retrieve Porting Order**: `GET /v2/porting_orders/{id}` — [API reference](https://developers.telnyx.com/api/porting/get-porting-order)

## Webhook Events Handled

This app handles these webhook events:
- `porting_order.status_changed` -- Porting order status updated (FOC date set, completed, rejected)
- `number_order.complete` -- Phone number order completed and ready to use

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/porting-order-tracker-dashboard-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (120 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/porting/orders` | Orders |
| `POST` | `/porting/bulk` | Bulk |
| `GET` | `/porting/orders` | Orders |
| `POST` | `/webhooks/porting` | Telnyx webhook handler |
| `GET` | `/porting/sla-check` | Sla Check |
| `GET` | `/porting/dashboard` | Dashboard |
| `GET` | `/health` | Health check |

### Key Functions

- **`check_sla_breach()`** — check sla breach
- **`submit_order()`** — submit order
- **`bulk_submit()`** — bulk submit
- **`list_orders()`** — list orders
- **`handle_webhook()`** — handle webhook
- **`sla_check()`** — sla check
- **`dashboard()`** — dashboard
- **`health()`** — health

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
curl -X POST http://localhost:5000/porting/orders \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t porting-order-tracker-dashboard-python .
docker run --env-file .env -p 5000:5000 porting-order-tracker-dashboard-python
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
