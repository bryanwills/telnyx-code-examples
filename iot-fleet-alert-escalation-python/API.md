## `POST /alert`

Receive alert.

### Response `200`

```json
{
  "error": "No sensor data"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/alert \
  -H "Content-Type: application/json" \
  -d '{"error": "No sensor data"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /alerts`

List all alerts.

### Response `200`

```json
{"alerts": alerts[-50:], "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/alerts
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "No payload"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `briefing`, `call_ended`, `event_received`, `listening`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "alerts": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
