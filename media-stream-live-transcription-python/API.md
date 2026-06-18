# API Reference — Media Stream Live Transcription

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/transcripts/<ccid>` | Get transcript. |
| `GET` | `/transcripts` | List transcripts. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /transcripts/<ccid>`

Get a specific transcript by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /transcripts`

List all transcripts.

### Response `200`

```json
{
  "error": "Not found"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active": "<string>",
  "transcripts": "<string>"
}
```

---

## Status Values

Records use these status values: `answering`, `ended`, `ok`, `streaming`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "active": "example-value",
  "completed": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
