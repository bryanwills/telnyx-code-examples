## `POST /webhooks/assistant`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/assistant
```

## `POST /setup`

Setup assistant.

### Response `200`

```json
{
  "error": "No payload"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/setup \
  -H "Content-Type: application/json" \
  -d '{"error": "No payload"}'
```

---

## `GET /analytics`

Get a specific analytics by ID.

### Response `200`

```json
{
  "status": "created",
  "assistant_id": "example-value"
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
  "total_calls": "example-value",
  "ai_resolution_rate": "example-value",
  "transfer_rate": "example-value",
  "department_distribution": "example-value",
  "ab_test_results": "example-value",
  "recent_calls": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `created`, `event_received`, `insights_recorded`, `ok`, `tracked`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "total_calls": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
