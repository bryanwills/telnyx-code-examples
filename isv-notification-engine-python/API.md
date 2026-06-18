# API Reference — ISV Notification Engine

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/notify` | Notify. |
| `POST` | `/notify/bulk` | Bulk notify. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/customers` | List customers. |
| `PUT` | `/customers/<cid>/preference` | Update preference. |
| `GET` | `/notifications` | List notifications. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /notify`

Notify.

### Request

```json
{ "status": "ok", "data": { } }
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

---

## `POST /notify/bulk`

Bulk notify.

### Request

```json
{ "status": "ok", "data": { } }
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

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.answered` | Begins interaction (TTS greeting or gather) |

---

## `GET /customers`

List all customers.

### Response `200`

```json
{"customers": null}
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
{ "status": "ok", "data": { } }
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

---

## Status Values

Records use these status values: `delivered`, `failed`, `ok`, `pending`

## Error Handling

All endpoints return JSON. On error:

```json
{ "status": "ok", "data": { } }
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
