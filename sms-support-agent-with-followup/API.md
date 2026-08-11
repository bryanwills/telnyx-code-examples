## `POST /webhooks/sms`

Receives Telnyx `message.received` webhooks. Routes to the per-phone-number actor.

### Request (Telnyx webhook payload)

```json
{
  "data": {
    "event_type": "message.received",
    "payload": {
      "from": {"phone_number": "+17177247292"},
      "to": [{"phone_number": "+16282564655"}],
      "text": "How do I send an SMS?"
    }
  }
}
```

### Response `200`

```json
{
  "action": "queued",
  "from": "+17177247292"
}
```

---

## `POST /debug/message`

Simulate an inbound SMS without a messaging profile (for testing).

### Request

```json
{
  "from": "+17177247292",
  "to": "+16282564655",
  "text": "How do I send an SMS?"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | `string` | no | Sender number (default: test number) |
| `to` | `string` | no | Recipient number (default: campaign number) |
| `text` | `string` | no | Message text (default: test text) |

### Response `200`

```json
{
  "action": "queued",
  "from": "+17177247292",
  "to": "+16282564655"
}
```

**Try it:**

```bash
curl -X POST https://sms-support-agent-<id>.telnyxcompute.com/debug/message \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","to":"+16282564655","text":"hi"}'
```

---

## `GET /health/{liveness,readiness}`

Health check endpoints.

### Response `200`

```
ok
```

**Try it:**

```bash
curl https://sms-support-agent-<id>.telnyxcompute.com/health/liveness
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing fields or unexpected event |
| `404` | Unknown route |
| `500` | Server error |
