## `POST /conferences/create`

Create a new conference.

### Request

```json
{
  "name": "Jane Smith",
  "participants": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | no | Display name or label |
| `participants` | `array` | no | List of participant phone numbers |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/conferences/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "participants": ["+12125559999"]}'
```

---

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

## `POST /webhooks/media`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/media
```

## `GET /conferences`

List all conferences.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/conferences
```

---

## `GET /conferences/<name>/transcript`

Get a specific transcript by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/conferences/example-id/transcript
```

---

## `POST /conferences/<name>/ask`

Ask ai.

### Request

```json
{
  "question": "question-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `string` | no | Question |

### Response `200`

```json
{
  "error": "not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/conferences/example-id/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "question-value"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answered`, `answering`, `dialing`, `hangup`, `joined`, `left`, `listening`, `ok`, `processed`, `received`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "active_conferences": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
