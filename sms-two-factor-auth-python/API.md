# API Reference — Production-ready OTP 2FA system with Flask and Telnyx SMS.

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/request-otp` | Request otp. |
| `POST` | `/auth/verify-otp` | Verify otp endpoint. |
| `GET` | `/auth/otp-status` | Otp status. |

---

## `POST /auth/request-otp`

Request otp.

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

## `POST /auth/verify-otp`

Verify otp endpoint.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | Phone number |
| `code` | `string` | **yes** | Code |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /auth/otp-status`

Otp status.

### Response `200`

```json
{
  "error": "Missing required query parameter: 'phone_number"
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
