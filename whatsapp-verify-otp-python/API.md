# API Reference — WhatsApp Verify OTP

All endpoints accept and return JSON. Base URL in local development: `http://localhost:5000`.

---

## `POST /verify/start`

Start a WhatsApp OTP verification for a phone number.

### Request

```json
{
  "phone_number": "+12125551234"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | E.164 formatted phone number to verify |

### Response `200`

```json
{
  "status": "sent",
  "phone": "+12125551234",
  "channel": "whatsapp"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | `sent` on success |
| `phone` | `string` | The phone number the OTP was sent to |
| `channel` | `string` | Delivery channel (`whatsapp`) |

**Try it:**

```bash
curl -X POST http://localhost:5000/verify/start \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12125551234"}'
```

---

## `POST /verify/check`

Submit the OTP code received via WhatsApp for verification.

### Request

```json
{
  "phone_number": "+12125551234",
  "code": "12345"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | The phone number that received the OTP |
| `code` | `string` | **yes** | The OTP code entered by the user |

### Response `200`

```json
{
  "status": "verified"
}
```

### Response `400`

```json
{
  "status": "invalid_code"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/verify/check \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12125551234", "code": "12345"}'
```

---

## `POST /webhooks/verify`

Inbound webhook endpoint called by Telnyx when a verification event occurs.

### Webhook Events

| Event | Description |
|-------|-------------|
| `verify.sent` | OTP message sent to the carrier/WhatsApp |
| `verify.delivered` | OTP message delivered to the user's device |
| `verify.completed` | User successfully verified the code |
| `verify.failed` | Delivery or verification failed |

### Request (from Telnyx)

```json
{
  "data": {
    "event_type": "verify.delivered",
    "payload": {
      "phone_number": "+12125551234"
    }
  }
}
```

### Response `200`

```json
{
  "status": "ok"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "verifications": 0
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Verification records use these status values: `pending`, `sent`, `delivered`, `completed`, `verified`, `failed`, `invalid_code`

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `401` | Invalid API key |
| `500` | Server error |
