## `POST /scan`

Scan numbers.

### Response `200`

```json
{"scanned": "<string>", "results": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/scan \
  -H "Content-Type: application/json" \
  -d '{"scanned": "<string>", "results": null}'
```

---

## `GET /health-report`

Health check and service status.

### Response `200`

```json
{
  "scanned": "example-value",
  "results": []
}
```

**Try it:**

```bash
curl http://localhost:5000/health-report
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "numbers": "example-value",
  "rotations": "example-value"
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
  "numbers_tracked": "example-value",
  "rotations": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
