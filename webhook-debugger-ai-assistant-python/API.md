# API Reference — Webhook Debugger AI Assistant

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/catch/<path:subpath>` | Catch webhook. |
| `POST` | `/catch/<path:subpath>` | Catch webhook. |
| `PUT` | `/catch/<path:subpath>` | Catch webhook. |
| `DELETE` | `/catch/<path:subpath>` | Catch webhook. |
| `GET` | `/analyze/<int:index>` | Analyze webhook. |
| `GET` | `/analyze/recent` | Analyze recent. |
| `GET` | `/log` | View log. |
| `GET` | `/health` | Health check and service status. |

---

## `GET /catch/<path:subpath>`

Catch webhook.

### Response `200`

```json
{"status": "caught", "id": "<string>" - 1}
```

---

## `GET /analyze/<int:index>`

Analyze webhook.

### Response `200`

```json
{
  "status": "caught",
  "id": "abc-123-def-456"
}
```

---

## `GET /analyze/recent`

Analyze recent.

### Response `200`

```json
{
  "error": "Not found"
}
```

---

## `GET /log`

View log.

### Response `200`

```json
{
  "error": "No webhooks captured yet"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "webhooks": "example-value",
  "total": 3
}
```

---

## Status Values

Records use these status values: `caught`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "webhooks_captured": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
