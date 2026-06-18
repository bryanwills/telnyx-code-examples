## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.initiated` | Call setup started |
| `call.answered` | Begins interaction (TTS greeting or gather) |
| `call.streaming.started` | Event processed |
| `call.streaming.stopped` | Event processed |
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

## `POST /calls/<call_id>/analyze`

Force analyze.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/example-id/analyze \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /calls`

List all calls.

### Response `200`

```json
{
        "total": "<string>",
        "flagged": "<string>",
        "calls": "<string>" or 0, reverse=true)
    }
```

**Try it:**

```bash
curl http://localhost:5000/calls
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `analyzed`, `cleared`, `completed`, `deepfake_detected`, `ok`, `recording`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Call not found"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
