## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /inventory`

List all inventory.

### Response `200`

```json
{"items": items[-50:], "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/inventory
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "items": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `cataloged`, `ignored`, `listed`, `ok`

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
