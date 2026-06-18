## `POST /appointments`

Create a new appointment.

### Request

```json
{
  "name": "Jane Smith",
  "phone": "+12125559999",
  "date": "2026-07-15",
  "time": "14:00",
  "provider": "provider-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |
| `date` | `string` | **yes** | Date (YYYY-MM-DD format) |
| `time` | `string` | **yes** | Time (HH:MM format) |
| `provider` | `string` | no | Provider |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/appointments \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "phone": "+12125559999", "date": "2026-07-15", "time": "14:00", "provider": "provider-value"}'
```

---

## `POST /confirm/<aid>`

Send confirmation.

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/confirm/example-id \
  -H "Content-Type: application/json" \
  -d '{"error": "Not found"}'
```

---

## `POST /escalate/<aid>`

Escalate to voice.

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/escalate/example-id \
  -H "Content-Type: application/json" \
  -d '{"error": "Not found"}'
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

### DTMF Options

| Key | Action |
|-----|--------|
| `1` | Confirmed |
| `2` | Reschedule Requested |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /appointments/status`

Appointment status.

### Response `200`

```json
{"appointments": "<string>", "summary": null, "confirmations": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/appointments/status
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "appointments": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `confirmed`, `ended`, `greeting`, `handled`, `ignored`, `listening`, `ok`, `pending`, `reschedule_requested`, `sms_sent`, `voice_calling`

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
