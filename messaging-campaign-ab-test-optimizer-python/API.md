## `POST /campaigns`

Create a new campaign.

### Request

```json
{
  "name": "Jane Smith",
  "variants": [],
  "contacts": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | no | Display name or label |
| `variants` | `array` | no | Variants |
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
  -d '{"name": "Jane Smith", "variants": [], "contacts": []}'
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

## `GET /campaigns/<cid>/analyze`

Analyze campaign.

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/campaigns/example-id/analyze
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "campaigns": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `created`, `ok`, `sent`

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
