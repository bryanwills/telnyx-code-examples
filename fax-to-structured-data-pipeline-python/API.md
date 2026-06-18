## `POST /webhooks/fax`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/fax
```

## `POST /extract`

Extract data.

### Request

```json
{
  "text": "Hello from the API",
  "type": "type-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | no | Text content |
| `type` | `string` | no | Type |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the API", "type": "type-value"}'
```

---

## `GET /faxes`

List all faxes.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/faxes
```

---

## `GET /extracted`

List all extracted.

### Response `200`

```json
{
  "faxes": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/extracted
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "faxes": "<string>",
  "extracted": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `ok`, `queued`, `received`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "data": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
