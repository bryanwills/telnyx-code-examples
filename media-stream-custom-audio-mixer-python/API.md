# API Reference — Media Stream Custom Audio Mixer

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `POST` | `/streams/<ccid>/inject` | Inject audio. |
| `GET` | `/streams` | List streams. |
| `GET` | `/stream-log` | Get log. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

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

---

## `GET /streams`

List all streams.

### Response `200`

```json
{
  "error": "invalid request body"
}
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

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "log": "example-value"
}
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
