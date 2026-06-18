# Global IP Failover Monitor

> Global IP Failover Monitor — monitor Global IP endpoints across regions, auto-failover between healthy endpoints.

## What You'll Build

A production-ready **global ip failover monitor** built with Python, Flask, and Migration, Networking, Number Porting.

| | |
|---|---|
| **Lines of code** | 93 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Networking, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **List Global IPs**: `GET /v2/global_ips` — [API reference](https://developers.telnyx.com/api/global-ips/list-global-ips)
- **Get IP Health**: `GET /v2/global_ips/{id}` — [API reference](https://developers.telnyx.com/api/global-ips/get-global-ip)
- **Send Alert SMS**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/global-ip-failover-monitor-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (93 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/endpoints` | Endpoints |
| `POST` | `/endpoints` | Endpoints |
| `POST` | `/check` | Check |
| `GET` | `/failover-log` | Failover Log |
| `GET` | `/regions` | Regions |
| `GET` | `/health` | Health check |

### Key Functions

- **`list_endpoints()`** — list endpoints
- **`add_endpoint()`** — add endpoint
- **`run_health_check()`** — run health check
- **`get_failover_log()`** — get failover log
- **`regions()`** — regions
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
curl -X GET http://localhost:5000/endpoints \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t global-ip-failover-monitor-python .
docker run --env-file .env -p 5000:5000 global-ip-failover-monitor-python
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
