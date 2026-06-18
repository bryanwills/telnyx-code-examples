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

## `GET /appointments`

List all appointments.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/appointments
```

---

## `POST /appointments/<int:idx>/approve`

Approve appointment.

### Response `200`

```json
{
  "appointments": [],
  "pending_review": "example-value"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/appointments/<int:idx>/approve \
  -H "Content-Type: application/json" \
  -d '{"appointments": [], "pending_review": "example-value"}'
```

---

## `POST /appointments/<int:idx>/reject`

Reject appointment.

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
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/appointments/<int:idx>/reject \
  -H "Content-Type: application/json" \
  -d '{"reason": "reason-value"}'
```

---

## `POST /copay/create`

Create a new copay.

### Request

```json
{
  "error": "Not found"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | `string` | no | Provider |
| `amount_cents` | `string` | no | Amount cents |
| `amount_cents` | `string` | no | Amount cents |

### Response `200`

```json
{
  "payment_link": "example-value"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/copay/create \
  -H "Content-Type: application/json" \
  -d '{"error": "Not found"}'
```

---

## `GET /slots`

Get a specific slots by ID.

### Response `200`

```json
{
  "available": []
}
```

**Try it:**

```bash
curl http://localhost:5000/slots
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "appointments": "<string>",
  "pending": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `confirmed`, `ok`, `pending_review`, `rejected`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "appointments": "example-value",
  "pending": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
