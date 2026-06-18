## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /memos`

List all memos.

### Response `200`

```json
{"memos": memos[-20:]}
```

**Try it:**

```bash
curl http://localhost:5000/memos
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "memos": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `ended`, `greeting`, `ok`, `processed`, `recording`

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
