## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "No payload"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `call_ended`, `event_received`, `ok`, `transcribing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active_calls": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
