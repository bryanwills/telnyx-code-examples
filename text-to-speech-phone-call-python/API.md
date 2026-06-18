## `POST /calls/initiate`

Initiate call endpoint.

### Request

```json
{
  "to": "+12125559999"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number (E.164) |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/initiate \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125559999"}'
```

---

## `POST /calls/<call_control_id>/speak`

Speak endpoint.

### Request

```json
{
  "text": "Hello from the API",
  "language": "language-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | **yes** | Text content |
| `language` | `string` | no | Language code (e.g., `en-US`) |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/example-id/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from the API", "language": "language-value"}'
```

---

## `POST /calls/<call_control_id>/hangup`

Hangup endpoint.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/example-id/hangup \
  -H "Content-Type: application/json" \
  -d '{"error": "Invalid API key"}'
```

---

## `POST /webhooks/call`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/call
```

## `GET /calls/status`

Get calls status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/calls/status
```

---

## Status Values

Records use these status values: `answered`, `hangup_initiated`, `initiated`, `received`, `speak_ended`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "active_calls": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
