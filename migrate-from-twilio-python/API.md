# API Reference — Migrate from Twilio

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/audit/twilio` | Audit twilio. |
| `POST` | `/migrate/messaging-profile` | Migrate messaging. |
| `POST` | `/migrate/numbers` | Migrate numbers. |
| `POST` | `/migrate/webhook-map` | Receives Telnyx webhook events. |
| `GET` | `/migrate/code-changes` | Code changes guide. |
| `GET` | `/migration-log` | Get log. |
| `GET` | `/health` | Health check and service status. |

---

## `GET /audit/twilio`

Audit twilio.

### Response `200`

```json
{
  "error": "TWILIO_ACCOUNT_SID not configured"
}
```

---

## `POST /migrate/messaging-profile`

Migrate messaging.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | no | Display name or label |
| `webhook_url` | `string` | no | Webhook url |

### Response `200`

```json
{
  "error": "Error description"
}
```

---

## `POST /migrate/numbers`

Migrate numbers.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numbers` | `array` | no | List of phone numbers |
| `authorized_person` | `string` | **yes** | Authorized person |

### Response `200`

```json
{"results": null}
```

---

## `POST /migrate/webhook-map`

Receives Telnyx webhook events.

---

## `GET /migrate/code-changes`

Code changes guide.

### Response `200`

```json
{"guide": {
        "sdk": "pip install telnyx (replaces twilio package)",
        "auth": "Bearer token header (replaces Account SID + Auth Token basic auth)",
        "voice": {"twilio": ""<string>"."<string>"", "telnyx": "call.actions."<string>""}
```

---

## `GET /migration-log`

Get a specific log by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "migrations": "<string>"
}
```

---

## Status Values

Records use these status values: `failed`, `ok`, `port_submitted`

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
