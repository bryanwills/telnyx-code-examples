# API Reference — Production-ready Flask application for sending bulk SMS via Telnyx.

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sms/bulk/send` | Send bulk sms endpoint. |
| `GET` | `/sms/bulk/status` | Bulk sms status. |

---

## `POST /sms/bulk/send`

Send bulk sms endpoint.

### Request

```json
{
  "recipients": [
    "+12125559999"
  ],
  "message": "Hello from the API"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recipients` | `array` | no | List of phone numbers (E.164) |
| `message` | `string` | **yes** | Message content to send |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /sms/bulk/status`

Bulk sms status.

### Response `200`

```json
{
  "service": "Telnyx Bulk SMS",
  "status": "operational",
  "rate_limit": "example-value",
  "delay_between_messages": "example-value"
}
```

---

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
