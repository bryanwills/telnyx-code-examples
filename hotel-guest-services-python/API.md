## `POST /webhooks/sms`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/sms
```

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.initiated` | Call setup started |
| `call.answered` | Begins interaction (TTS greeting or gather) |
| `call.speak.ended` | TTS finished — transitions to gather or next step |
| `call.gather.ended` | Input received — processes customer response |
| `call.hangup` | Call ended — cleans up session state |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /requests`

List all requests.

### Response `200`

```json
{"requests": null}
```

**Try it:**

```bash
curl http://localhost:5000/requests
```

---

## `POST /requests/<int:idx>/complete`

Complete request.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/requests/<int:idx>/complete \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "open": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `completed`, `ok`, `open`

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
