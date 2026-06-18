## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /standups`

List all standups.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/standups
```

---

## `GET /standups/summary`

Daily summary.

### Response `200`

```json
{
  "message": "No updates today"
}
```

**Try it:**

```bash
curl http://localhost:5000/standups/summary
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "updates": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `ended`, `greeting`, `listening`, `ok`, `responding`, `waiting`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "message": "No updates today"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
