## `POST /webhooks/sms`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/sms
```

## `GET /returns`

List all returns.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/returns
```

---

## `POST /returns/<int:idx>/approve`

Manual approve.

### Request

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent` | `string` | no | Agent |
| `refund_amount` | `number` | no | Refund amount |
| `payment_intent` | `string` | no | Payment intent |

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/returns/<int:idx>/approve \
  -H "Content-Type: application/json" \
  -d '{"id": "abc-123", "status": "active", "created_at": "2026-06-18T21:00:00Z"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "returns": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `auto_approved`, `escalated`, `evaluating`, `exchange_offered`, `manually_approved`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "returns": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
