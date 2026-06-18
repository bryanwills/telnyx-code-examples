## `POST /sessions/start`

Start coaching.

### Request

```json
{
  "customer": "customer-value",
  "rep": "rep-value",
  "context": "context-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer` | `string` | **yes** | Customer |
| `rep` | `string` | **yes** | Rep |
| `context` | `string` | no | Context |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"customer": "customer-value", "rep": "rep-value", "context": "context-value"}'
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

## `POST /webhooks/media`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/media
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

## `GET /sessions/<name>`

Get a specific session by ID.

### Response `200`

```json
{
  "status": "received"
}
```

**Try it:**

```bash
curl http://localhost:5000/sessions/example-id
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answered`, `briefing_rep`, `dialing_customer`, `dialing_rep`, `ended`, `hangup`, `live`, `no_session`, `ok`, `processed`, `received`, `spoke`, `starting`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active_sessions": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
