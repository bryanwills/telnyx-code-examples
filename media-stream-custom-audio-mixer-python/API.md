## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `POST /streams/<ccid>/inject`

Inject audio.

### Request

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio_url` | `string` | **yes** | Audio url |
| `overlay` | `boolean` | no | Overlay |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/streams/example-id/inject \
  -H "Content-Type: application/json" \
  -d '{"id": "abc-123", "status": "active", "created_at": "2026-06-18T21:00:00Z"}'
```

---

## `GET /streams`

List all streams.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/streams
```

---

## `GET /stream-log`

Get a specific log by ID.

### Response `200`

```json
{
  "active_streams": [],
  "count": 3
}
```

**Try it:**

```bash
curl http://localhost:5000/stream-log
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "log": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `ended`, `injecting`, `ok`, `streaming`, `streaming_started`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active_streams": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
