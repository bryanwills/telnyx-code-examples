## `GET /lookup/<number>`

Lookup number.

### Response `200`

```json
{
  "result": "example-value",
  "source": "cache"
}
```

**Try it:**

```bash
curl http://localhost:5000/lookup/example-id
```

---

## `POST /lookup/batch`

Batch lookup.

### Request

```json
{
  "numbers": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numbers` | `array` | no | List of phone numbers |

### Response `200`

```json
{"results": null, "total": "<string>"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/lookup/batch \
  -H "Content-Type: application/json" \
  -d '{"numbers": ["+12125559999"]}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /enrichments`

List all enrichments.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/enrichments
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "cached": "<string>",
  "enrichments": "<string>"
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
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
