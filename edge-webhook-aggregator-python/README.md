---
name: edge-webhook-aggregator
title: "Edge Webhook Aggregator"
description: "Multi-tenant webhook consolidation at the edge."
language: python
framework: flask
telnyx_products: [Edge Compute, Voice, Messaging]
channel: [voice, sms]
---

# Edge Webhook Aggregator

> Also known as: webhook batching, multi-tenant webhooks, event aggregation, webhook proxy, event consolidation.

Multi-tenant webhook consolidation at the edge. Receives all Telnyx voice and messaging events, classifies by tenant from phone number mapping, batches events per interval, and forwards one consolidated payload per tenant.

## Telnyx API Endpoints Used

- See code for API calls

## Telnyx Webhook Events

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):



## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `moonshotai/Kimi-K2.6` | no | AI model | [Models](https://developers.telnyx.com/docs/inference/models) |
| `PORT` | `integer` | `5000` | no | Server port | -- |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-webhook-aggregator-python
cp .env.example .env
pip install -r requirements.txt
python app.py
```

### Webhook Configuration

1. Expose your local server: `ngrok http 5000`
2. Configure in [Telnyx Portal](https://portal.telnyx.com/call-control/applications):
   - Call Control Application -> Webhook URL -> `https://<id>.ngrok.io/webhooks/voice`

## API Reference

### `POST /tenants`

Tenants.

```bash
curl -X POST http://localhost:5000/tenants \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

**Response:**

```json
{"status": "ok"}
```

### `GET /tenants`

Tenants.

```bash
curl http://localhost:5000/tenants
```

**Response:**

```json
{"status": "ok", "service": "edge-webhook-aggregator"}
```

### `GET /stats`

Stats.

```bash
curl http://localhost:5000/stats
```

**Response:**

```json
{"status": "ok", "service": "edge-webhook-aggregator"}
```

### `GET /health`

Health.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{"status": "ok", "service": "edge-webhook-aggregator"}
```


## Webhook Endpoints

### `POST /webhooks/voice`

Telnyx sends call events here. Your app processes them and responds with the next action.

**Events handled:**



**Example payload:**

```json
{
  "data": {
    "event_type": "call.initiated",
    "id": "evt_123",
    "payload": {
      "call_control_id": "v3:abc123",
      "direction": "incoming",
      "from": "+12125551234",
      "to": "+18005559876"
    }
  }
}
```

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/ingest` | Ingest |
| `POST` | `/tenants` | Tenants |
| `GET` | `/tenants` | Tenants |
| `GET` | `/stats` | Stats |
| `GET` | `/health` | Health |

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
