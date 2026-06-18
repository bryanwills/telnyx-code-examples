## `GET /analytics/calls`

Call analytics.

### Response `200`

```json
{
  "period_days": [],
  "total_calls": 3,
  "inbound": "example-value",
  "outbound": "example-value",
  "avg_duration_secs": "example-value",
  "total_minutes": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/analytics/calls
```

---

## `GET /analytics/numbers`

Number analytics.

### Response `200`

```json
{
  "total_numbers": "example-value",
  "by_status": []
}
```

**Try it:**

```bash
curl http://localhost:5000/analytics/numbers
```

---

## `GET /analytics/messaging`

Messaging analytics.

### Response `200`

```json
{
  "recent_messages": "example-value",
  "sent": "example-value",
  "received": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/analytics/messaging
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
