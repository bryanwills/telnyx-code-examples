## `POST /webinars`

Create a new webinar.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | no | Title |
| `max_participants` | `string` | no | Max participants |
| `title` | `string` | **yes** | Title |
| `host` | `string` | **yes** | Host |
| `scheduled` | `string` | **yes** | Scheduled |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/webinars \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `GET /webinars/<room_id>/recordings`

Get a specific recordings by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/webinars/example-id/recordings
```

---

## `POST /recordings/<recording_id>/transcribe`

Transcribe recording.

### Request

```json
{
  "transcript": "transcript-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | `string` | no | Transcript |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/recordings/example-id/transcribe \
  -H "Content-Type: application/json" \
  -d '{"transcript": "transcript-value"}'
```

---

## `GET /webinars`

List all webinars.

### Response `200`

```json
{"webinars": "<string>")}
```

**Try it:**

```bash
curl http://localhost:5000/webinars
```

---

## `GET /recordings`

List all processed.

### Response `200`

```json
{"recordings": recordings[-20:]}
```

**Try it:**

```bash
curl http://localhost:5000/recordings
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "webinars": "<string>",
  "recordings": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `ok`, `scheduled`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "webinars": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
