# API Reference — Ai Real Time Translation Bridge

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/bridge` | Create a new bridge. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/bridges` | List bridges. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /bridge`

Create a new bridge.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number_a` | `string` | **yes** | Number a |
| `lang_a` | `string` | no | Lang a |
| `number_b` | `string` | **yes** | Number b |
| `lang_b` | `string` | no | Lang b |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /bridges`

List all bridges.

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
  "active_bridges": "example-value"
}
```

---

## Status Values

Records use these status values: `calling_a`, `ended`, `listening`, `ok`, `translated`

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
