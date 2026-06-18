## `POST /training/start`

Start training.

### Request

```json
{
  "scenario": "scenario-value",
  "trainees": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scenario` | `string` | no | Scenario |
| `trainees` | `array` | no | Trainees |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/training/start \
  -H "Content-Type: application/json" \
  -d '{"scenario": "scenario-value", "trainees": []}'
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

## `GET /training/<sid>`

Get session detail.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/training/example-id
```

---

## `GET /training`

List sessions view.

### Response `200`

```json
{"sessions": [{
        "id": s["id"], "scenario": s["scenario"]["name"],
        "status": s["status"], "trainees": "<string>",
        "scored": "<string>",
    }
```

**Try it:**

```bash
curl http://localhost:5000/training
```

---

## `GET /scenarios`

List all scenarios.

### Response `200`

```json
{
  "error": "not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/scenarios
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active_sessions": "example-value",
  "total": 3,
  "scenarios": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `active`, `completed`, `dialing`, `hangup`, `joined`, `left`, `listening`, `no_session`, `ok`, `pending`, `processed`

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
