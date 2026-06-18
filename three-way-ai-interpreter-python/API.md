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

**Try it:**

```bash
curl -X POST http://localhost:5000/interpret/start \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
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

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /sessions`

List all sessions.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/sessions
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

**Try it:**

```bash
curl http://localhost:5000/sessions/example-id/transcript
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

**Try it:**

```bash
curl http://localhost:5000/health
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
