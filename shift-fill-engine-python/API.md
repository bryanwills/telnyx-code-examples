## `POST /shifts/open`

Open shift.

### Request

```json
{
  "role": "role-value",
  "date": "2026-07-15",
  "time": "14:00",
  "department": "department-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `role` | `string` | no | Role |
| `date` | `string` | **yes** | Date (YYYY-MM-DD format) |
| `time` | `string` | **yes** | Time (HH:MM format) |
| `department` | `string` | no | Department |

### Response `200`

```json
{"shift": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/shifts/open \
  -H "Content-Type: application/json" \
  -d '{"role": "role-value", "date": "2026-07-15", "time": "14:00", "department": "department-value"}'
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

### DTMF Options

| Key | Action |
|-----|--------|
| `1` | Filled |
| `2` | No problem. Thanks for letting us know. |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /shifts`

List all shifts.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/shifts
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "open": "<string>",
  "filled": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `calling`, `filled`, `ok`, `unfilled`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
