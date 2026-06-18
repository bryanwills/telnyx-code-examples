## `POST /scan`

Scan fleet.

### Response `200`

```json
{
  "error": "No SIM data available"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/scan \
  -H "Content-Type: application/json" \
  -d '{"error": "No SIM data available"}'
```

---

## `GET /anomalies`

List all anomalies.

### Response `200`

```json
{"anomalies": anomalies[-100:]}
```

**Try it:**

```bash
curl http://localhost:5000/anomalies
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

**Try it:**

```bash
curl http://localhost:5000/health
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
