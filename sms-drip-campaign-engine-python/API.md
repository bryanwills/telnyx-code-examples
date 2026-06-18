## `POST /drip/create`

Create a new drip.

### Request

```json
{
  "name": "Jane Smith",
  "steps": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `steps` | `array` | no | Steps |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/drip/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "steps": []}'
```

---

## `POST /drip/<did>/subscribe`

Subscribe.

### Request

```json
{
  "phone": "+12125559999"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/drip/example-id/subscribe \
  -H "Content-Type: application/json" \
  -d '{"phone": "+12125559999"}'
```

---

## `POST /drip/advance`

Advance all.

### Response `200`

```json
{"advanced": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/drip/advance \
  -H "Content-Type: application/json" \
  -d '{"advanced": null}'
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

### SMS Commands

| Reply | Action |
|-------|--------|
| `STOP` | Get |

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

Records use these status values: `handled`, `ignored`, `ok`, `subscribed`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "advanced": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
