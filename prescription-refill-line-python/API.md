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

## `GET /refills`

List all refills.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/refills
```

---

## `POST /refills/<int:idx>/approve`

Approve refill.

### Request

```json
{
  "refills": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pickup_time` | `string` | no | Pickup time |

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/refills/<int:idx>/approve \
  -H "Content-Type: application/json" \
  -d '{"refills": []}'
```

---

## `POST /refills/<int:idx>/deny`

Deny refill.

### Request

```json
{
  "reason": "reason-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | `string` | no | Reason |

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/refills/<int:idx>/deny \
  -H "Content-Type: application/json" \
  -d '{"reason": "reason-value"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "pending": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `approved`, `denied`, `ok`, `pending_pharmacist`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "pending": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
