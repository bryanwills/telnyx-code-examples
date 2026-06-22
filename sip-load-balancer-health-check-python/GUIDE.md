# Build a SIP Load Balancer Health Check

SIP Load Balancer Health Check — monitor SIP trunk health across multiple endpoints, auto-failover to healthy trunks, track uptime metrics.

## How It Works

```
  SIP Endpoints (3+)
    │   │   │
    ▼   ▼   ▼
  ┌──────────────────────────┐
  │ Health Check Loop         │
  │ • TCP probe per endpoint  │
  │ • Uptime tracking         │
  │ • Weighted routing table  │
  └────────────┬──────────────┘
               │
      ┌────────┼────────┐
      ▼        ▼        ▼
  Primary  Secondary  Tertiary
  (70%)    (20%)      (10%)
               │
               ▼
  Auto-failover on health failure
  SMS alert to admin
```

## Telnyx Products Used

- **Migration**
- **Number Porting** — phone number search, purchase, and configuration

## API Endpoints

- **List SIP Connections**: `GET /v2/sip_connections` — [API reference](https://developers.telnyx.com/api/sip-connections/list-sip-connections)
- **Send Alert SMS**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/sip-load-balancer-health-check-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (73 lines). Here's what each piece does.

### Business Logic

- **`health_check()`** — Health check endpoint for monitoring and load balancer probes.
- **`get_route()`** — Fetches route by ID with full details.
- **`list_endpoints()`** — Fetches route by ID with full details.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/check` | Health Check |
| `GET` | `/route` | Get Route |
| `GET` | `/endpoints` | List Endpoints |
| `GET` | `/endpoints` | Add Endpoint |
| `GET` | `/log` | Get Log |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def health_check():
    results = []
    for name, ep in endpoints.items():
        ep["uptime_checks"] += 1
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ep["host"], ep["port"]))
            sock.close()
            healthy = result == 0
        except Exception:
```

The main endpoint processes the request:

```python
def health_check():
    results = []
    for name, ep in endpoints.items():
        ep["uptime_checks"] += 1
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ep["host"], ep["port"]))
            sock.close()
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
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production SIP Trunk",
    "domain": "sip.example.com"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/route | python3 -m json.tool
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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sip-load-balancer-health-check-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
