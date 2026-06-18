## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /queue`

Get a specific queue by ID.

### Response `200`

```json
{"queue": [{"name": c["name"], "topic": c["topic"], "position": i+1}
```

**Try it:**

```bash
curl http://localhost:5000/queue
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "queue": "<string>",
  "active": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `ended`, `greeting`, `listening`, `ok`, `processing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
