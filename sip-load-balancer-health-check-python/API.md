## `POST /check`

Health check.

### Response `200`

```json
{"results": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"results": null}'
```

---

## `GET /route`

Get a specific route by ID.

### Response `200`

```json
{
  "error": "No healthy endpoints",
  "fallback": "primary"
}
```

**Try it:**

```bash
curl http://localhost:5000/route
```

---

## `GET /endpoints`

List all endpoints.

### Response `200`

```json
{"endpoints": {n: {"host": e["host"], "status": e["status"],
        "uptime": "<string>" * 100, 1)}
```

**Try it:**

```bash
curl http://localhost:5000/endpoints
```

---

## `POST /endpoints`

Add endpoint.

### Request

```json
{
  "name": "Jane Smith",
  "host": "host-value",
  "port": "port-value",
  "weight": "weight-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `host` | `string` | **yes** | Host |
| `port` | `string` | no | Port |
| `weight` | `string` | no | Weight |

### Response `200`

```json
{
  "status": "added"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/endpoints \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "host": "host-value", "port": "port-value", "weight": "weight-value"}'
```

---

## `GET /log`

Get a specific log by ID.

### Response `200`

```json
{
  "results": []
}
```

**Try it:**

```bash
curl http://localhost:5000/log
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{"status": "ok", "healthy": null, "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `added`, `healthy`, `ok`, `unknown`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "No healthy endpoints",
  "fallback": "primary"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
