## `POST /invoices`

Add invoice.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `company` | `string` | **yes** | Company |
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |
| `amount` | `number` | no | Amount in dollars |
| `due_date` | `string` | **yes** | Due date |
| `payment_link` | `string` | no | Payment link |

### Response `200`

```json
{"invoice": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/invoices \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /reminders/run`

Run reminders.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `days_overdue` | `string` | no | Days overdue |

### Response `200`

```json
{"results": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/reminders/run \
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

## `GET /invoices`

List all invoices.

### Response `200`

```json
{"invoices": null}
```

**Try it:**

```bash
curl http://localhost:5000/invoices
```

---

## `POST /invoices/<int:idx>/paid`

Mark paid.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/invoices/<int:idx>/paid \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "unpaid": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `ok`, `paid`, `unpaid`

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
