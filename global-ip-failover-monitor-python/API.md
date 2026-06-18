## `GET /endpoints`

List all endpoints.

### Response `200`

```json
{"endpoints": "<string>")}
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
  "endpoints": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | no | Id |
| `ip_address` | `string` | **yes** | Ip address |
| `region` | `string` | **yes** | Region |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/endpoints \
  -H "Content-Type: application/json" \
  -d '{"endpoints": "example-value"}'
```

---

## `POST /check`

Run health check.

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

## `GET /failover-log`

Get failover log.

### Response `200`

```json
{
  "results": []
}
```

**Try it:**

```bash
curl http://localhost:5000/failover-log
```

---

## `GET /regions`

Regions.

### Response `200`

```json
{
  "log": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/regions
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `added`, `healthy`, `ok`, `unhealthy`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "endpoints": "example-value",
  "healthy": 3,
  "failovers": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
