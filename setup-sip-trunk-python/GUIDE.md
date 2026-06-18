# Set Up a SIP Trunk with Telnyx

Provision and configure a SIP trunk connection on Telnyx with codec preferences, authentication, and failover.

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

- **SIP Trunking** — SIP trunking with codec and routing configuration

## API Endpoints

- **Create SIP Connection**: `POST /v2/sip_connections` -- [API reference](https://developers.telnyx.com/api/sip/create-sip-connection)
- **List SIP Connections**: `GET /v2/sip_connections` -- [API reference](https://developers.telnyx.com/api/sip/list-sip-connections)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/setup-sip-trunk-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (70 lines). Here's what each piece does.

### Business Logic

- **`setup_sip_endpoint()`** — Processes setup sip endpoint request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/sip/setup` | Setup Sip Endpoint |

The trigger endpoint kicks off the workflow:

```python
def setup_sip_endpoint():
    """HTTP endpoint to set up SIP trunking."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    name = data.get("name")
    username = data.get("username")
    password = data.get("password")
```

Helper function that handles the core action:

```python
def create_sip_connection(name: str, username: str, password: str) -> dict:
    """Create SIP connection via Telnyx and return JSON-serializable response data."""
    # Validate input to prevent API errors
    if not name or not username or not password:
        raise ValueError("Name, username, and password are required")
    
    # Use client.sip_connections.create() — NOT client.sip_connections.create()
    response = client.sip_connections.create(
        name=name,
        username=username,
        password=password,
    )
    
    # Extract serializable data — SDK objects are NOT JSON-serializable
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
curl -X POST http://localhost:5000/sip/setup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production SIP Trunk",
    "domain": "sip.example.com"
  }'
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
docker build -t setup-sip-trunk-python .
docker run --env-file .env -p 5000:5000 setup-sip-trunk-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
