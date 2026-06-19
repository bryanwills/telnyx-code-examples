---
description: Route inbound SIP calls to different destinations based on caller, DID,
  or time-of-day rules.
framework: flask
language: python
name: inbound-sip-routing
telnyx_products:
- SIP Trunking
- Voice
title: Flask application for managing inbound SIP routing with Telnyx.
---



# Flask application for managing inbound SIP routing with Telnyx.

> Also known as: SIP call routing, inbound DID routing, SIP trunk call handling, PBX inbound routing.

Application. Built with Telnyx Migration, Number Porting.

## Telnyx API Endpoints Used

- **Create SIP Connection**: `POST /v2/sip_connections` — [API reference](https://developers.telnyx.com/api/sip-connections/create-sip-connection)
- **List SIP Connections**: `GET /v2/sip_connections` — [API reference](https://developers.telnyx.com/api/sip-connections/list-sip-connections)
- **Retrieve SIP Connection**: `GET /v2/sip_connections/{id}` — [API reference](https://developers.telnyx.com/api/sip-connections/get-sip-connection)

## Architecture

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

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `FLASK_DEBUG` | `string` | `false` | no | Flask debug | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/inbound-sip-routing-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `GET /sip/connections`

List all SIP connections configured for inbound routing.

```bash
curl http://localhost:5000/sip/connections
```

**Response:**

```json
{
  "connections": [
    {
      "id": "1494404757140276705",
      "name": "Production SIP",
      "status": "active",
      "ip": "192.168.1.100"
    }
  ]
}
```

### `POST /sip/connections`

Create a new SIP connection for inbound call routing.

```bash
curl -X POST http://localhost:5000/sip/connections \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "connections": [
    {
      "id": "1494404757140276705",
      "name": "Production SIP",
      "status": "active",
      "ip": "192.168.1.100"
    }
  ]
}
```

### `GET /sip/connections/<connection_id>`

Get detailed information about a specific SIP connection.

```bash
curl http://localhost:5000/sip/connections/example-id
```

**Response:**

```json
{
  "connections": [
    {
      "id": "1494404757140276705",
      "name": "Production SIP",
      "status": "active",
      "ip": "192.168.1.100"
    }
  ]
}
```

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
