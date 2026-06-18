# API Reference — Storage Voicemail Archive

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/voicemails` | List voicemails. |
| `GET` | `/voicemails/search` | Search voicemails. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /voicemails`

List all voicemails.

### Response `200`

```json
{"voicemails": voicemails[-50:]}
```

---

## `GET /voicemails/search`

Search voicemails.

### Response `200`

```json
{"results": null}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "voicemails": "<string>"
}
```

---

## Status Values

Records use these status values: `answering`, `archived`, `ended`, `greeting`, `ok`, `recording`

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
