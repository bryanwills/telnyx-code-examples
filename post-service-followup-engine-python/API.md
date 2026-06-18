## `POST /follow-up/send`

Send followup.

### Request

```json
{
  "phone": "+12125559999",
  "service": "service-value",
  "tech": "tech-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |
| `service` | `string` | no | Service or appointment type |
| `tech` | `string` | no | Tech |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/follow-up/send \
  -H "Content-Type: application/json" \
  -d '{"phone": "+12125559999", "service": "service-value", "tech": "tech-value"}'
```

---

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
| `call.answered` | Begins interaction (TTS greeting or gather) |
| `call.speak.ended` | TTS finished — transitions to gather or next step |
| `call.gather.ended` | Input received — processes customer response |
| `call.hangup` | Call ended — cleans up session state |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /follow-ups`

List all followups.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/follow-ups
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

Records use these status values: `completed`, `negative_followup`, `ok`, `rated`, `sent`, `survey_sent`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "follow_ups": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
