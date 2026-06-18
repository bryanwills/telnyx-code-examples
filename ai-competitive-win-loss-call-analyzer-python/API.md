## `POST /analyze`

Analyze call.

### Request

```json
{
  "transcript": "transcript-value",
  "outcome": "outcome-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | `string` | no | Transcript |
| `outcome` | `string` | no | Outcome |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"transcript": "transcript-value", "outcome": "outcome-value"}'
```

---

## `GET /insights`

Get a specific insights by ID.

### Response `200`

```json
{
  "error": "No analyses yet"
}
```

**Try it:**

```bash
curl http://localhost:5000/insights
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "analyses": "<string>"
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
  "analyses": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
