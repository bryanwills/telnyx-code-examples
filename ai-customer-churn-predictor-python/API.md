## `POST /predict`

Predict churn.

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"status": "ok"}'
```

---

## `POST /predict/batch`

Batch predict.

### Request

```json
{
  "customers": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customers` | `array` | no | Customers |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"customers": []}'
```

---

## `GET /predictions`

List all predictions.

### Response `200`

```json
{"predictions": null}
```

**Try it:**

```bash
curl http://localhost:5000/predictions
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "predictions": "<string>"
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
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
