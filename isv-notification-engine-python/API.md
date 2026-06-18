## `POST /notify`

Notify.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer_id` | `string` | **yes** | Customer id |
| `message` | `string` | no | Message content to send |
| `urgency` | `string` | no | Urgency |

### Response `200`

```json
{"notification": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/notify \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /notify/bulk`

Bulk notify.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer_ids` | `string` | no | Customer ids |
| `message` | `string` | no | Message content to send |
| `urgency` | `string` | no | Urgency |

### Response `200`

```json
{"results": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/notify/bulk \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.answered` | Begins interaction (TTS greeting or gather) |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /customers`

List all customers.

### Response `200`

```json
{"customers": null}
```

**Try it:**

```bash
curl http://localhost:5000/customers
```

---

## `PUT /customers/<cid>/preference`

Update preference.

### Request

```json
{
  "preference": "preference-value",
  "fallback": "fallback-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `preference` | `string` | no | Preference |
| `fallback` | `string` | no | Fallback |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X PUT http://localhost:5000/customers/example-id/preference \
  -H "Content-Type: application/json" \
  -d '{"preference": "preference-value", "fallback": "fallback-value"}'
```

---

## `GET /notifications`

List all notifications.

### Response `200`

```json
{"notifications": notifications[-100:], "stats": {
        "total": "<string>", "delivered": "<string>",
        "failed": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/notifications
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "notifications": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `delivered`, `failed`, `ok`, `pending`

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
