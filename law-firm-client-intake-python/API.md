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

## `GET /intakes`

List all intakes.

### Response `200`

```json
{"intakes": null}
```

**Try it:**

```bash
curl http://localhost:5000/intakes
```

---

## `POST /intakes/<int:idx>/accept`

Accept intake.

### Request

```json
{
  "attorney": "attorney-value",
  "time": "14:00"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `attorney` | `string` | no | Attorney |
| `time` | `string` | no | Time (HH:MM format) |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/intakes/<int:idx>/accept \
  -H "Content-Type: application/json" \
  -d '{"attorney": "attorney-value", "time": "14:00"}'
```

---

## `POST /intakes/<int:idx>/decline`

Decline intake.

### Request

```json
{
  "reason": "reason-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | `string` | no | Reason |

### Response `200`

```json
{
  "intakes": []
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/intakes/<int:idx>/decline \
  -H "Content-Type: application/json" \
  -d '{"reason": "reason-value"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "intakes": "<string>",
  "pending": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `accepted`, `declined`, `ok`, `pending_review`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Not found"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
