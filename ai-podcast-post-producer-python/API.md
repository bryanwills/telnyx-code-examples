# API Reference — AI Podcast Post-Producer

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `POST` | `/produce` | Produce episode. |
| `GET` | `/episodes` | List episodes. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `POST /produce`

Produce episode.

### Request

```json
{
  "transcript": "transcript-value",
  "title": "title-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | `string` | no | Transcript |
| `title` | `string` | no | Title |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /episodes`

List all episodes.

### Response `200`

```json
{"episodes": episodes[-20:]}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "episodes": "<string>"
}
```

---

## Status Values

Records use these status values: `answering`, `ended`, `ok`, `recorded`, `recording`, `saved`

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
