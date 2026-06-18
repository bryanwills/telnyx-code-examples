## `POST /campaigns`

Create a new campaign.

### Request

```json
{
  "name": "Jane Smith",
  "message": "Hello from the API"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `message` | `string` | **yes** | Message content to send |

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
  -d '{"name": "Jane Smith", "message": "Hello from the API"}'
```

---

## `POST /subscribers`

Add subscribers.

### Request

```json
{
  "numbers": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numbers` | `array` | no | List of phone numbers |

### Response `200`

```json
{"added": null, "total": "<string>"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/subscribers \
  -H "Content-Type: application/json" \
  -d '{"numbers": ["+12125559999"]}'
```

---

## `POST /campaigns/<cid>/send`

Send campaign.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/campaigns/example-id/send \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /subscribers`

List all subscribers.

### Response `200`

```json
{
  "error": "Campaign not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/subscribers
```

---

## `GET /campaigns`

List all campaigns.

### Response `200`

```json
{"campaigns": "<string>")}
```

**Try it:**

```bash
curl http://localhost:5000/campaigns
```

---

## `GET /analytics`

Analytics.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/analytics
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "campaigns": "<string>",
  "subscribers": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `draft`, `ok`, `opted_in`, `opted_out`, `sent`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "total": 3,
  "active": "example-value",
  "opted_out": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
