---
name: wireless-fleet-activation-portal
title: "Wireless Fleet Activation Portal — bulk activate SIMs with status tracking."
description: "Wireless Fleet Activation Portal — bulk activate SIMs with status tracking."
language: python
framework: flask
telnyx_products: [IoT/SIM]
---

# Wireless Fleet Activation Portal — bulk activate SIMs with status tracking.

Wireless Fleet Activation Portal — bulk activate SIMs with status tracking.

## Telnyx API Endpoints Used

- **SIM Cards**: `GET /v2/sim_cards` — [API reference](https://developers.telnyx.com/api/sim-cards/list-sim-cards)

## Architecture

```
  ┌──────────────────┐
  │ API Request      │
  │ (SIM data /       │
  │  sensor reading)   │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Threshold Check   │
  └────────┬─────────┘
           │
           ▼
     JSON response
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/wireless-fleet-activation-portal-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `GET /sims`

Returns sims

```bash
curl http://localhost:5000/sims
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `POST /sims/activate`

Triggers activate

```bash
curl -X POST http://localhost:5000/sims/activate \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `POST /sims/deactivate`

Triggers deactivate

```bash
curl -X POST http://localhost:5000/sims/deactivate \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `GET /activation-log`

Returns activation-log

```bash
curl http://localhost:5000/activation-log
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /health`

Returns health

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "uptime_seconds": 3842,
  "active_sessions": 2,
  "version": "1.0.0"
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or missing API key | Verify `TELNYX_API_KEY` in `.env` matches your key in the [Portal](https://portal.telnyx.com/api-keys) |
| Webhook not received | Local server not publicly reachable | Expose it with a tunnel (e.g. ngrok) and set the webhook URL in the [Telnyx Portal](https://portal.telnyx.com) |
| `422 Unprocessable Entity` | Missing or malformed request fields | Check the request body against the API Reference above |

## Related Examples

- [Activate Sim Card (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/activate-sim-card-python/README.md)
- [IoT Fleet Alert Escalation (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/iot-fleet-alert-escalation-python/README.md)
- [IoT Panic Button Voice Alert (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/iot-panic-button-voice-alert-python/README.md)
- [IoT Smart Building Voice Control (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/iot-smart-building-voice-control-python/README.md)
- [Monitor IoT Data Usage (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/monitor-iot-data-usage-python/README.md)

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.
