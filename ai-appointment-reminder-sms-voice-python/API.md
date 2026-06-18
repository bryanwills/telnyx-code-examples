## `POST /appointments`

Add appointment.

### Response `200`

```json
{
  "status": "added",
  "total": "<string>"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/appointments \
  -H "Content-Type: application/json" \
  -d '{"status": "added", "total": "<string>"}'
```

---

## `POST /remind`

Trigger a new reminders.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/remind \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "reminders_sent": []
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `added`, `cancelled`, `confirmed`, `ended`, `greeting`, `handled`, `ignored`, `listening`, `no_appointment`, `ok`, `pending`, `reprompting`, `rescheduling`, `responding`

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
