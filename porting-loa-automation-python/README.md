---
name: porting-loa-automation
title: "Porting LOA Automation"
description: "Porting LOA Automation — automate Letter of Authorization generation and porting order submission."
language: python
framework: flask
telnyx_products: [Missions, Number Porting]
---

# Porting LOA Automation

Porting LOA Automation — automate Letter of Authorization generation and porting order submission.

## Telnyx API Endpoints Used

- **Create Porting Order**: `POST /v2/porting_orders` — [API reference](https://developers.telnyx.com/api/porting/create-porting-order)
- **List Porting Orders**: `GET /v2/porting_orders` — [API reference](https://developers.telnyx.com/api/porting/list-porting-orders)
- **Upload LOA**: `POST /v2/porting_orders/{id}/loa` — [API reference](https://developers.telnyx.com/api/porting/upload-loa)

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx Number Porting
           │
           ├──► Order tracking
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
cd telnyx-code-examples/porting-loa-automation-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /loa/generate`

Triggers generate

```bash
curl -X POST http://localhost:5000/loa/generate \
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

### `POST /loa/submit-and-port`

Triggers submit-and-port

```bash
curl -X POST http://localhost:5000/loa/submit-and-port \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "porting_orders": [
    {
      "id": "port-abc123",
      "numbers": ["+12125551234"],
      "status": "submitted",
      "target_date": "2026-07-22"
    }
  ]
}
```

### `POST /loa/check-portability`

Triggers check-portability

```bash
curl -X POST http://localhost:5000/loa/check-portability \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125551234",
    "channel": "sms"
  }'
```

**Response:**

```json
{
  "verification_id": "ver-abc123",
  "status": "pending",
  "channel": "sms",
  "phone": "+12125551234"
}
```

### `GET /loa`

Returns loa

```bash
curl http://localhost:5000/loa
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

### `GET /pipeline`

Returns pipeline

```bash
curl http://localhost:5000/pipeline
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

- [Branded Caller Id Manager (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/branded-caller-id-manager-python/README.md)
- [Build Conference Calling (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/build-conference-calling-python/README.md)
- [Build IVR Phone Menu (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/build-ivr-phone-menu-python/README.md)
- [Bulk Number Validation Cleaner (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/bulk-number-validation-cleaner-python/README.md)
- [Call Analytics Dashboard Api (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/call-analytics-dashboard-api-python/README.md)

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.
