## `POST /check`

Health check.

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"status": "ok"}'
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

**Try it:**

```bash
curl http://localhost:5000/status
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

**Try it:**

```bash
curl http://localhost:5000/health
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
