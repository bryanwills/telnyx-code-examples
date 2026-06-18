# API Reference — Autonomous Outbound Sales Agent

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/leads` | Add leads. |
| `POST` | `/campaign/start` | Start campaign. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/results` | Get results. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /leads`

Add leads.

### Request

```json
{
  "leads": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `leads` | `array` | no | Leads |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /campaign/start`

Start campaign.

### Request

```json
{
  "error": "No leads in queue"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `call_control_id` | `string` | **yes** | Call control id |

### Response `200`

```json
{
  "error": "No leads in queue"
}
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /results`

Get a specific results by ID.

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
  "results": [],
  "remaining_leads": "example-value"
}
```

---

## Status Values

Records use these status values: `active`, `call_ended`, `calling`, `dialing`, `event_received`, `greeting`, `listening`, `ok`, `reprompting`, `responding`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active_calls": "example-value",
  "leads_queued": "example-value",
  "completed": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
