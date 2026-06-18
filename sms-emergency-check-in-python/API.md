## `POST /monitor`

Add monitored.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |
| `name` | `string` | no | Display name or label |
| `emergency_contact` | `string` | no | Emergency contact |

### Response `200`

```json
{"status": "monitoring", "phone": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/monitor \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /check-in/send`

Send check ins.

### Response `200`

```json
{"sent": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/check-in/send \
  -H "Content-Type: application/json" \
  -d '{"sent": null}'
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `POST /check-in/escalate`

Escalate missed.

### Response `200`

```json
{"escalated": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/check-in/escalate \
  -H "Content-Type: application/json" \
  -d '{"escalated": null}'
```

---

## `GET /status`

Get a specific status by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/status
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "monitored": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `escalated`, `handled`, `ignored`, `monitoring`, `ok`, `sent`, `unknown`, `waiting`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "sent": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
