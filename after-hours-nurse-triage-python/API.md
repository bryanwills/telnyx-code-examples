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

## `GET /triage/queue`

Get a specific queue by ID.

### Response `200`

```json
{"queue": null, "counts": {
        "emergency": "<string>",
        "urgent": "<string>",
        "routine": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/triage/queue
```

---

## `POST /triage/<int:idx>/override`

Override severity.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `severity` | `string` | no | Severity |
| `nurse_name` | `string` | no | Nurse name |
| `note` | `string` | no | Note |

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/triage/<int:idx>/override \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "queue_size": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `advised_911`, `ok`, `paged_oncall`, `pending_review`, `queued_callback`, `reviewed`

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
