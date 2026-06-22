# API Reference -- Edge Merge Reference Checker

Base URL: `http://localhost:5000`

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/check` | Check |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/reports` | Reports |
| `GET` | `/reports/<check_id>` | <Check Id> |
| `GET` | `/health` | Health |

---

## `POST /check`

Check.

### Request

```json
{"example": "value"}
```

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

---

## `POST /webhooks/voice`

Telnyx webhook handler.

### Events Handled

| Event | Description |
|-------|-------------|
| `call.answered` | Call connected, app begins interaction with greeting |
| `call.gather.ended` | Caller input received (speech or DTMF), app processes response |
| `call.speak.ended` | TTS playback finished, transitions to next action |
| `call.hangup` | Call ended, cleans up session state and logs outcome |

### Response `200`

```json
{"status": "ok"}
```

---

## `GET /reports`

Reports.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/reports
```

---

## `GET /reports/<check_id>`

<Check Id>.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/reports/<check_id>
```

---

## `GET /health`

Health.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/health
```

---

## Error Handling

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|--------|
| `200` | Success |
| `400` | Bad request |
| `404` | Not found |
| `500` | Server error |
