## `GET /audit/twilio`

Audit twilio.

### Response `200`

```json
{
  "error": "TWILIO_ACCOUNT_SID not configured"
}
```

**Try it:**

```bash
curl http://localhost:5000/audit/twilio
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

**Try it:**

```bash
curl -X POST http://localhost:5000/migrate/messaging-profile \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
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

**Try it:**

```bash
curl -X POST http://localhost:5000/migrate/numbers \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /migrate/webhook-map`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/migrate/webhook-map
```

## `GET /migrate/code-changes`

Code changes guide.

### Response `200`

```json
{"guide": {
        "sdk": "pip install telnyx (replaces twilio package)",
        "auth": "Bearer token header (replaces Account SID + Auth Token basic auth)",
        "voice": {"twilio": ""<string>"."<string>"", "telnyx": "call.actions."<string>""}
```

**Try it:**

```bash
curl http://localhost:5000/migrate/code-changes
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

**Try it:**

```bash
curl http://localhost:5000/migration-log
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

**Try it:**

```bash
curl http://localhost:5000/health
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
