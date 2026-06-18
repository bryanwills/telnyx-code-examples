## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /keywords`

List all keywords.

### Response `200`

```json
{"keywords": {k: {"response": v["response"], "hits": v["count"]}
```

**Try it:**

```bash
curl http://localhost:5000/keywords
```

---

## `POST /keywords`

Add keyword.

### Request

```json
{
  "keyword": "keyword-value",
  "response": "response-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keyword` | `string` | no | Keyword |
| `response` | `string` | no | Response |

### Response `200`

```json
{"status": "added", "keyword": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/keywords \
  -H "Content-Type: application/json" \
  -d '{"keyword": "keyword-value", "response": "response-value"}'
```

---

## `GET /analytics`

Analytics.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/analytics
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "keywords": "<string>",
  "messages": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `added`, `handled`, `ignored`, `ok`

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
