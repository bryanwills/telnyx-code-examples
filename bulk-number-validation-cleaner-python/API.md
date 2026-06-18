## `POST /validate`

Validate numbers.

### Request

```json
{
  "numbers": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numbers` | `array` | no | List of phone numbers |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/validate \
  -H "Content-Type: application/json" \
  -d '{"numbers": ["+12125559999"]}'
```

---

## `GET /validate/single/<number>`

Validate single.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/validate/single/example-id
```

---

## `GET /jobs`

List all jobs.

### Response `200`

```json
{"jobs": null}
```

**Try it:**

```bash
curl http://localhost:5000/jobs
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "jobs": "<string>"
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
  "jobs": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
