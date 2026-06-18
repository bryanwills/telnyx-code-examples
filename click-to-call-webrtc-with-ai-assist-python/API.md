## `GET /`

Index.

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl http://localhost:5000/
```

---

## `POST /webrtc/token`

Get a specific token by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/webrtc/token \
  -H "Content-Type: application/json" \
  -d '{"error": "Error description"}'
```

---

## `POST /coaching`

Get a specific coaching by ID.

### Request

```json
{
  "transcript": "transcript-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | `string` | no | Transcript |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/coaching \
  -H "Content-Type: application/json" \
  -d '{"transcript": "transcript-value"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
