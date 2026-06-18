# WireGuard Private Voice Network

> WireGuard Private Voice Network — create WireGuard mesh network for private SIP trunking with encrypted voice traffic.

## What You'll Build

A production-ready **wireguard private voice network** built with Python, Flask, and Migration, Networking, Number Porting.

| | |
|---|---|
| **Lines of code** | 95 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Networking, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Create WireGuard Interface**: `POST /v2/wireguard_interfaces` — [API reference](https://developers.telnyx.com/api/networking/create-wireguard-interface)
- **List WireGuard Interfaces**: `GET /v2/wireguard_interfaces` — [API reference](https://developers.telnyx.com/api/networking/list-wireguard-interfaces)
- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/wireguard-private-voice-network-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (95 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/networks` | Networks |
| `GET` | `/networks` | Networks |
| `POST` | `/interfaces` | Interfaces |
| `POST` | `/peers` | Peers |
| `GET` | `/interfaces/<iface_id>/config` | Config |
| `GET` | `/topology` | Topology |
| `GET` | `/health` | Health check |

### Key Functions

- **`create_network()`** — create network
- **`list_networks()`** — list networks
- **`create_interface()`** — create interface
- **`create_peer()`** — create peer
- **`get_config()`** — get config
- **`topology()`** — topology
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
curl -X POST http://localhost:5000/networks \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t wireguard-private-voice-network-python .
docker run --env-file .env -p 5000:5000 wireguard-private-voice-network-python
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
