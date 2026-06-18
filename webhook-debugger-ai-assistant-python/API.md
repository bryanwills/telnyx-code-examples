## `GET /catch/<path:subpath>`

Catch webhook.

### Response `200`

```json
{"status": "caught", "id": "<string>" - 1}
```

**Try it:**

```bash
curl http://localhost:5000/catch/<path:subpath>
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

**Try it:**

```bash
curl http://localhost:5000/analyze/<int:index>
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

**Try it:**

```bash
curl http://localhost:5000/analyze/recent
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

**Try it:**

```bash
curl http://localhost:5000/log
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

**Try it:**

```bash
curl http://localhost:5000/health
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
