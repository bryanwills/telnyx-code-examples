## `POST /webhooks/call`

Receives Telnyx Call Control webhook events for AI agent routing.

### Events Handled

| Event | Action |
|-------|--------|
| `call.initiated` | Answer incoming call |
| `call.answered` | Connect to AI agent (gather speech) |
| `call.gather.ended` | Send speech to AI, play response |
| `call.speak.ended` | Resume listening for next input |
| `call.hangup` | Clean up session |

**Test with curl:**

```bash
curl -X POST http://localhost:5000/webhooks/call \
  -H "Content-Type: application/json" \
  -d '{"data":{"event_type":"call.initiated","payload":{"call_control_id":"abc-123","from":"+12125551234"}}}'
```

## Status Values

Records use these status values: `answered`, `call_answered`, `call_ended`, `event_received`, `hangup_initiated`, `message_finished`

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
