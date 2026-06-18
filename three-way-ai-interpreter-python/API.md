# API Reference — Three-Way Call with AI Interpreter

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/interpret/start` | Start session. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/sessions` | List sessions. |
| `GET` | `/sessions/<sid>/transcript` | Get transcript. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /interpret/start`

Start session.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `party_a` | `string` | **yes** | Party a |
| `party_b` | `string` | **yes** | Party b |
| `language_a` | `string` | no | Language a |
| `language_b` | `string` | no | Language b |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.answered` | Begins interaction (TTS greeting or gather) |
| `call.speak.ended` | TTS finished — transitions to gather or next step |
| `call.gather.ended` | Input received — processes customer response |
| `call.hangup` | Call ended — cleans up session state |

---

## `GET /sessions`

List all sessions.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /sessions/<sid>/transcript`

Get a specific transcript by ID.

### Response `200`

```json
{
  "error": "not found"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active_sessions": "example-value",
  "total": 3
}
```

---

## Status Values

Records use these status values: `answered`, `dialing`, `ended`, `listening`, `live`, `no_session`, `ok`, `translated`

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
