## `POST /drop`

Voicemail drop.

### Request

```json
{
  "numbers": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numbers` | `array` | no | List of phone numbers |

### Response `200`

```json
{"results": null, "total": "<string>"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/drop \
  -H "Content-Type: application/json" \
  -d '{"numbers": ["+12125559999"]}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /drops`

List all drops.

### Response `200`

```json
{"drops": drops[-100:], "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/drops
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `calling`, `delivered`, `ended`, `failed`, `human_answered_skipped`, `initiated`, `message_playing`, `ok`, `processed`

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
