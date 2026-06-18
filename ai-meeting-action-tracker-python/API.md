## `POST /meetings/create`

Create a new meeting.

### Request

```json
{
  "title": "title-value",
  "participants": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | no | Title |
| `participants` | `array` | no | List of participant phone numbers |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/meetings/create \
  -H "Content-Type: application/json" \
  -d '{"title": "title-value", "participants": ["+12125559999"]}'
```

---

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

## `GET /meetings/<mid>`

Get a specific meeting by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/meetings/example-id
```

---

## `GET /meetings`

List all meetings.

### Response `200`

```json
{
  "error": "not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/meetings
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{"status": "ok", "active": null, "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `active`, `completed`, `dialing`, `joined`, `left`, `listening`, `no_meeting`, `ok`, `pending`, `processed`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
