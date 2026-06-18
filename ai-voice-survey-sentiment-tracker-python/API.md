# API Reference — AI Voice Survey Sentiment Tracker

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/results` | Get results. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /results`

Get a specific results by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active": "<string>",
  "completed": "<string>"
}
```

---

## Status Values

Records use these status values: `answering`, `asking`, `ended`, `listening`, `ok`, `processing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "results": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
