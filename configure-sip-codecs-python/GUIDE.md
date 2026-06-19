# Build a Production-ready Flask application for SIP codec configuration via Telnyx

Configure SIP trunk codec preferences, order, and negotiate settings for optimal voice quality.

## How It Works

```
  Your PBX / SBC
        │
        ▼
  ┌──────────────────┐
  │ Telnyx SIP Trunk  │
  │ (IP / FQDN auth)  │
  └────────┬─────────┘
           │
           ▼
     PSTN / Telnyx Network
```

## Telnyx Products Used

- **Migration**
- **Number Porting** — phone number search, purchase, and configuration
- **SIP Trunking** — SIP trunking with codec and routing configuration

## API Endpoints

- **Create SIP Connection**: `POST /v2/sip_connections` — [API reference](https://developers.telnyx.com/api/sip-connections/create-sip-connection)
- **Retrieve SIP Connection**: `GET /v2/sip_connections/{id}` — [API reference](https://developers.telnyx.com/api/sip-connections/get-sip-connection)
- **List SIP Connections**: `GET /v2/sip_connections` — [API reference](https://developers.telnyx.com/api/sip-connections/list-sip-connections)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/configure-sip-codecs-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (229 lines). Here's what each piece does.

### Starting the Workflow

**`create_connection()`** — Kicks off the main workflow. Validates the request, creates the record, and initiates the Telnyx API calls.

```python
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400
    name = data.get("name")
    codecs = data.get("codecs", ["G.711"])
    username = data.get("username")
    password = data.get("password")
    sip_endpoint = data.get("sip_endpoint")
```

### Business Logic

- **`list_connections()`** — Returns all SIP connections with codec settings.
- **`get_connection()`** — Fetches a single SIP connection by ID.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/sip/connections` | List Connections |
| `GET` | `/sip/connections` | Create Connection |
| `GET` | `/sip/connections/<connection_id>` | Get Connection |

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

**Check results:**

```bash
curl http://localhost:5000/sip/connections | python3 -m json.tool
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
docker build -t configure-sip-codecs-python .
docker run --env-file .env -p 5000:5000 configure-sip-codecs-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
