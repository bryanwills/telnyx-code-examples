# API Reference — Global Lead Response Engine

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/leads` | Get leads. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /leads`

Get a specific leads by ID.

### Response `200`

```json
{
  "error": "No payload"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "leads": "example-value",
  "total": 3
}
```

---

## Status Values

Records use these status values: `answering`, `call_ended`, `event_received`, `greeting`, `listening`, `no_call`, `ok`, `reprompting`, `responding`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active_calls": "example-value",
  "leads_qualified": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
