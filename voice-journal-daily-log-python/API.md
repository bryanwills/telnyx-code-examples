## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /journal`

List all entries.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/journal
```

---

## `GET /journal/insights`

Insights.

### Response `200`

```json
{
  "message": "No entries yet"
}
```

**Try it:**

```bash
curl http://localhost:5000/journal/insights
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "entries": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `captured`, `greeting`, `listening`, `ok`, `saved`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "entries": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
