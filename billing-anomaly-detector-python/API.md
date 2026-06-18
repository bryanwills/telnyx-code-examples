## `POST /config`

Set baselines.

### Response `200`

```json
{"baselines": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/config \
  -H "Content-Type: application/json" \
  -d '{"baselines": null}'
```

---

## `GET /config`

Get a specific baselines by ID.

### Response `200`

```json
{"baselines": null}
```

**Try it:**

```bash
curl http://localhost:5000/config
```

---

## `POST /check`

Run anomaly check.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /balance`

Check balance.

### Response `200`

```json
{
  "baselines": []
}
```

**Try it:**

```bash
curl http://localhost:5000/balance
```

---

## `GET /alerts`

List all alerts.

### Response `200`

```json
{"alerts": alerts[-50:]}
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
{"status": "ok", "alerts": "<string>", "baselines": null}
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
  "anomalies": [],
  "checked_at": "2026-06-18T21:00:00Z"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
