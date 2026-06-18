## `POST /survey/start`

Start survey.

### Request

```json
{
  "contacts": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contacts` | `array` | no | Contacts |

### Response `200`

```json
{
  "queued": "<string>"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/survey/start \
  -H "Content-Type: application/json" \
  -d '{"contacts": []}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /survey/results`

Get a specific results by ID.

### Response `200`

```json
{"results": null, "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/survey/results
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "completed": "<string>",
  "queued": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `asking`, `completed`, `listening`, `ok`, `processing`

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
