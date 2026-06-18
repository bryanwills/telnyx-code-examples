## `POST /reminders/send`

Send reminders.

### Response `200`

```json
{
  "reminders_sent": "example-value",
  "results": []
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/reminders/send \
  -H "Content-Type: application/json" \
  -d '{"reminders_sent": "example-value", "results": []}'
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

## `POST /webhooks/sms`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/sms
```

## `GET /clients`

List all clients.

### Response `200`

```json
{"clients": null}
```

**Try it:**

```bash
curl http://localhost:5000/clients
```

---

## `POST /clients/<int:idx>/doc-received`

Doc received.

### Request

```json
{
  "document": "document-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `document` | `string` | **yes** | Document |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/clients/<int:idx>/doc-received \
  -H "Content-Type: application/json" \
  -d '{"document": "document-value"}'
```

---

## `GET /readiness`

Readiness dashboard.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/readiness
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "clients": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `docs_pending`, `ok`, `ready`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "clients": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
