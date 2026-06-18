## `POST /campaigns`

Create a new campaign.

### Request

```json
{
  "name": "Jane Smith",
  "message": "Hello from the API",
  "contacts": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `message` | `string` | **yes** | Message content to send |
| `contacts` | `array` | no | Contacts |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "message": "Hello from the API", "contacts": []}'
```

---

## `POST /campaigns/<cid>/send`

Send campaign.

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/campaigns/example-id/send \
  -H "Content-Type: application/json" \
  -d '{"error": "Not found"}'
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

### SMS Commands

| Reply | Action |
|-------|--------|
| `STOP` | Get |
| `START` | start action |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /verification/status`

Verification status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/verification/status
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `created`, `handled`, `ignored`, `ok`, `sent`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "campaigns": "example-value",
  "opt_outs": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
