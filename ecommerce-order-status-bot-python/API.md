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

## `POST /exceptions/check`

Check exceptions.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tracking_number` | `string` | **yes** | Tracking number |
| `exception` | `string` | no | Exception |
| `customer_phone` | `string` | **yes** | Customer phone |
| `new_eta` | `string` | no | New eta |

### Response `200`

```json
{
  "status": "notified"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/exceptions/check \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /exceptions`

List all exceptions.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/exceptions
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "exceptions": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `any`, `notified`, `ok`, `shipped`

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
