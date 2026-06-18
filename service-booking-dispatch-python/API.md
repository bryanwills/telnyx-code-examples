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

## `GET /bookings`

List all bookings.

### Response `200`

```json
{"bookings": null}
```

**Try it:**

```bash
curl http://localhost:5000/bookings
```

---

## `POST /bookings/<int:idx>/assign`

Assign tech.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tech_name` | `string` | no | Tech name |

### Response `200`

```json
{
  "bookings": []
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/bookings/<int:idx>/assign \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /techs`

List all techs.

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/techs
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "bookings": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `assigned`, `ok`, `pending_deposit`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "bookings": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
