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

## `POST /waitlist/add`

Add to waitlist.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |
| `party_size` | `string` | no | Party size |
| `wait_minutes` | `string` | no | Wait minutes |

### Response `200`

```json
{"position": "<string>", "entry": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/waitlist/add \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /waitlist/<int:idx>/ready`

Table ready.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/waitlist/<int:idx>/ready \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /reservations`

List all reservations.

### Response `200`

```json
{"reservations": null}
```

**Try it:**

```bash
curl http://localhost:5000/reservations
```

---

## `GET /waitlist`

List all waitlist.

### Response `200`

```json
{"waitlist": [w for w in waitlist if w["status"] == "waiting"]}
```

**Try it:**

```bash
curl http://localhost:5000/waitlist
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "reservations": "<string>",
  "waitlist": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `confirmed`, `notified`, `ok`, `waiting`

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
