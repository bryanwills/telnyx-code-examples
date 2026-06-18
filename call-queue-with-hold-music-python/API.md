## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /queue`

Queue status.

### Response `200`

```json
{
  "error": "invalid request body"
}
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

Records use these status values: `answering`, `available`, `busy`, `ended`, `ok`, `routing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "queue_length": "example-value",
  "agents": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
