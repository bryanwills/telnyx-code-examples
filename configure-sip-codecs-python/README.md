---
name: configure-sip-codecs
title: "Production-ready Flask application for SIP codec configuration via Telnyx."
description: "Voice application. Built with Telnyx Migration, Number Porting, SIP Trunking."
language: python
framework: flask
telnyx_products: [Migration, Number Porting, SIP Trunking]
---

# Production-ready Flask application for SIP codec configuration via Telnyx.

Voice application. Built with Telnyx Migration, Number Porting, SIP Trunking.

## Architecture

```text
┌──────────┐     ┌────────────┐     ┌─────────────────┐
│ API Call  │────►│   Telnyx   │────►│   Your App      │
└──────────┘     │   Cloud    │     └────────┬────────┘
                └────────────┘               │
                                        Processing
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `SIP_USERNAME` | `string` | `your_value` | **yes** | Sip username | — |
| `SIP_PASSWORD` | `string` | `your_value` | **yes** | Sip password | — |
| `SIP_ENDPOINT` | `string` | `your_value` | **yes** | Sip endpoint | — |
| `FLASK_DEBUG` | `string` | `false` | no | Flask debug | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/configure-sip-codecs-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

### Docker

```bash
docker build -t configure-sip-codecs-python .
docker run --env-file .env -p 5000:5000 configure-sip-codecs-python
```

## API Reference

### `GET /sip/connections`

HTTP endpoint to list all SIP connections.

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

HTTP endpoint to create a new SIP connection with codec configuration.

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

HTTP endpoint to retrieve codec configuration for a specific SIP connection.

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
