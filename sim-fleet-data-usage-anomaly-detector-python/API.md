# API Reference — SIM Fleet Data Usage Anomaly Detector

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/scan` | Scan fleet. |
| `GET` | `/anomalies` | List anomalies. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /scan`

Scan fleet.

### Response `200`

```json
{
  "error": "No SIM data available"
}
```

---

## `GET /anomalies`

List all anomalies.

### Response `200`

```json
{"anomalies": anomalies[-100:]}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "anomalies": "example-value"
}
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "anomalies_detected": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
