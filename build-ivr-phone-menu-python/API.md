## `POST /webhooks/call`

Receives Telnyx Call Control webhook events for IVR menu navigation.

### Events Handled

| Event | Action |
|-------|--------|
| `call.initiated` | Answer the incoming call |
| `call.answered` | Play welcome greeting via TTS |
| `call.speak.ended` | Start gathering DTMF input |
| `call.gather.ended` | Route based on key pressed |
| `call.hangup` | Clean up session |

### DTMF Menu Options

| Key | Route |
|-----|-------|
| `1` | Sales department |
| `2` | Support department |
| `3` | Billing department |
| `0` | Repeat menu |

---

## `GET /webhooks/call/status`

Returns current IVR session status and active call count.

---

**Try it:**

```bash
curl http://localhost:5000/webhooks/call/status
```

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
