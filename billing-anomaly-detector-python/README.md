---
name: billing-anomaly-detector
title: "Billing Anomaly Detector"
description: "Billing Anomaly Detector — monitor usage and billing for anomalies, alert on cost spikes and unusual patterns."
language: python
framework: flask
telnyx_products: [CDR, SMS/MMS]
---

# Billing Anomaly Detector

Billing Anomaly Detector — monitor usage and billing for anomalies, alert on cost spikes and unusual patterns.

## Telnyx API Endpoints Used

- **List CDRs**: `GET /v2/reports/cdrs` — [API reference](https://developers.telnyx.com/api/call-detail-records/list-cdrs)
- **List MDRs**: `GET /v2/reports/mdrs` — [API reference](https://developers.telnyx.com/api/messaging-detail-records/get-messaging-detail-records)

## Architecture

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx CDR / Billing
           │
           ├──► Risk analysis
           │
           ▼
     JSON response
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `ALERT_WEBHOOK` | `string` | `your_value` | **yes** | Alert webhook | — |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/billing-anomaly-detector-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

## API Reference

### `POST /config`

Triggers config

```bash
curl -X POST http://localhost:5000/config \
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

### `GET /config`

Returns config

```bash
curl http://localhost:5000/config
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

### `POST /check`

Triggers check

```bash
curl -X POST http://localhost:5000/check \
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

### `GET /balance`

Returns balance

```bash
curl http://localhost:5000/balance
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

### `GET /alerts`

Returns alerts

```bash
curl http://localhost:5000/alerts
```

**Response:**

```json
{
  "alerts": [
    {
      "id": "alrt-98234",
      "transaction": "TXN-98234",
      "amount": 150.00,
      "risk_score": 85,
      "status": "verified",
      "verified_at": "2026-07-15T14:32:00Z"
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

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
