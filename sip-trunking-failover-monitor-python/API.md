# API Reference — SIP Trunking Failover Monitor

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/check` | Health check. |
| `GET` | `/status` | Get status. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /check`

Health check.

### Response `200`

```json
{ "status": "ok" }
```

---

## `GET /status`

Get a specific status by ID.

### Response `200`

```json
{
  "active_connection": "example-value",
  "primary_id": "example-value",
  "backup_id": "example-value",
  "recent_checks": "example-value"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active_trunk": "example-value",
  "checks": "example-value"
}
```

---

## Status Values

Records use these status values: `healthy`, `ok`, `unhealthy`

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
