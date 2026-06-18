## `POST /webhooks/sms`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages.

### Events Handled

| Event | Action |
|-------|--------|
| `message.received` | Log message, extract sender and text |
| `message.finalized` | Confirm delivery status |

### Example Webhook Payload

```json
{
  "data": {
    "event_type": "message.received",
    "payload": {
      "from": { "phone_number": "+12125551234" },
      "to": [{ "phone_number": "+14155559999" }],
      "text": "Hello from a customer"
    }
  }
}
```

**Test with curl:**

```bash
curl -X POST http://localhost:5000/webhooks/sms \
  -H "Content-Type: application/json" \
  -d '{"data":{"event_type":"message.received","payload":{"from":{"phone_number":"+12125551234"},"text":"test"}}}'
```

## Status Values

Records use these status values: `error`, `ignored`, `received`

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
