# API Reference — Verify Multi-Channel Auth

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/verify/start` | Start verification. |
| `POST` | `/verify/check` | Check verification. |
| `POST` | `/verify/escalate/<vid>` | Escalate channel. |
| `POST` | `/verify/cascade` | Cascade verify. |
| `GET` | `/verifications` | List verifications. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /verify/start`

Start verification.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | Phone number |
| `channel` | `string` | no | Communication channel (sms, voice, whatsapp) |
| `timeout` | `number` | no | Timeout |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /verify/check`

Check verification.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verification_id` | `string` | **yes** | Verification id |
| `code` | `string` | **yes** | Code |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /verify/escalate/<vid>`

Escalate channel.

### Response `200`

```json
{
  "error": "Verification not found"
}
```

---

## `POST /verify/cascade`

Cascade verify.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | Phone number |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /verifications`

List all verifications.

### Response `200`

```json
{"verifications": "<string>")[-20:]}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "verifications": "<string>"
}
```

---

## Status Values

Records use these status values: `failed`, `ok`, `pending`, `verified`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "verifications": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
