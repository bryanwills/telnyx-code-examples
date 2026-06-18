## `POST /webhooks/fax`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/fax
```

## `GET /faxes`

List all faxes.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/faxes
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "processed": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `ignored`, `ok`, `processed`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "faxes": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
