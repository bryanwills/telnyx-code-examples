## `POST /webhooks/call`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/call
```

## `GET /calls/status/<call_control_id>`

Get call status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/calls/status/example-id
```

---

## `POST /calls/hangup/<call_control_id>`

Hangup call endpoint.

### Response `200`

```json
{
  "call_control_id": "example-value",
  "is_alive": "example-value",
  "state": "example-value",
  "metadata": "example-value"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/hangup/example-id \
  -H "Content-Type: application/json" \
  -d '{"call_control_id": "example-value", "is_alive": "example-value", "state": "example-value", "metadata": "example-value"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "healthy"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answered`, `call_answered`, `call_ended`, `call_forwarded`, `event_ignored`, `hangup_initiated`, `healthy`, `transfer_initiated`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Invalid API key"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
