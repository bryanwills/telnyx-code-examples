## `POST /experiments`

Create a new experiment.

### Request

```json
{
  "variant_a": {},
  "variant_b": {},
  "split": "split-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `variant_a` | `object` | no | Variant a |
| `variant_b` | `object` | no | Variant b |
| `split` | `string` | no | Split |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/experiments \
  -H "Content-Type: application/json" \
  -d '{"variant_a": {}, "variant_b": {}, "split": "split-value"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /experiments/<eid>/results`

Get a specific results by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/experiments/example-id/results
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "experiments": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `ended`, `greeting`, `listening`, `ok`, `routed`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Not found"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
