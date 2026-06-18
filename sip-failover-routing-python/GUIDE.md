# Production-ready SIP failover routing system with Flask and Telnyx.

> Voice application. Built with Telnyx Migration, Number Porting.

## What You'll Build

A production-ready **production-ready sip failover routing system with flask and telnyx** built with Python, Flask, and Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 297 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **List Phone Numbers**: `GET /v2/phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-phone-numbers)

## Webhook Events Handled

This app handles these [Call Control](https://developers.telnyx.com/docs/api/v2/call-control) webhook events:
- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction
- `call.hangup` -- Call ended, app cleans up session

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/sip-failover-routing-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (297 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/sip/connections` | Connections |
| `POST` | `/sip/connections` | Connections |
| `GET` | `/sip/connections/<connection_id>` | <Connection Id> |
| `GET` | `/sip/health` | Health check |
| `GET` | `/sip/failover-status` | Failover Status |
| `POST` | `/webhooks/call` | Telnyx webhook handler |
| `POST` | `/sip/assign-number` | Assign Number |

### Key Functions

- **`create_sip_connection()`** — create sip connection
- **`list_sip_connections()`** — list sip connections
- **`get_sip_connection()`** — get sip connection
- **`check_endpoint_health()`** — check endpoint health
- **`get_active_endpoint()`** — get active endpoint
- **`assign_phone_number_to_connection()`** — assign phone number to connection
- **`list_connections()`** — list connections
- **`create_connection()`** — create connection
- **`get_connection()`** — get connection
- **`check_health()`** — check health

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
curl -X GET http://localhost:5000/sip/connections \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t sip-failover-routing-python .
docker run --env-file .env -p 5000:5000 sip-failover-routing-python
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
