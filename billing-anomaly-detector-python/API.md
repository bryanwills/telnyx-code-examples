# API Reference — Billing Anomaly Detector

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/config` | Set baselines. |
| `GET` | `/config` | Get baselines. |
| `POST` | `/check` | Run anomaly check. |
| `GET` | `/balance` | Check balance. |
| `GET` | `/alerts` | List alerts. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /config`

Set baselines.

### Response `200`

```json
{"baselines": null}
```

---

## `GET /config`

Get a specific baselines by ID.

### Response `200`

```json
{"baselines": null}
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

---

## `GET /balance`

Check balance.

### Response `200`

```json
{
  "baselines": []
}
```

---

## `GET /alerts`

List all alerts.

### Response `200`

```json
{"alerts": alerts[-50:]}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{"status": "ok", "alerts": "<string>", "baselines": null}
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
