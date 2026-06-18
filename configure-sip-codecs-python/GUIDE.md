# Production-ready Flask application for SIP codec configuration via Telnyx.

> Voice application. Built with Telnyx Migration, Number Porting, SIP Trunking.

## What You'll Build

A production-ready **production-ready flask application for sip codec configuration via telnyx** built with Python, Flask, and Migration, Number Porting, SIP Trunking.

| | |
|---|---|
| **Lines of code** | 229 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Number Porting, SIP Trunking |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Create SIP Connection**: `POST /v2/sip_connections` — [API reference](https://developers.telnyx.com/api/sip-connections/create-sip-connection)
- **Retrieve SIP Connection**: `GET /v2/sip_connections/{id}` — [API reference](https://developers.telnyx.com/api/sip-connections/get-sip-connection)
- **List SIP Connections**: `GET /v2/sip_connections` — [API reference](https://developers.telnyx.com/api/sip-connections/list-sip-connections)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/configure-sip-codecs-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (229 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/sip/connections` | Connections |
| `POST` | `/sip/connections` | Connections |
| `GET` | `/sip/connections/<connection_id>` | <Connection Id> |

### Key Functions

- **`create_sip_connection_with_codecs()`** — create sip connection with codecs
- **`get_sip_connection_codecs()`** — get sip connection codecs
- **`list_sip_connections()`** — list sip connections
- **`list_connections()`** — list connections
- **`create_connection()`** — create connection
- **`get_connection()`** — get connection

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
curl -X GET http://localhost:5000/sip/connections \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t configure-sip-codecs-python .
docker run --env-file .env -p 5000:5000 configure-sip-codecs-python
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
