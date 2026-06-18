## `POST /bridge`

Create a new bridge.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number_a` | `string` | **yes** | Number a |
| `lang_a` | `string` | no | Lang a |
| `number_b` | `string` | **yes** | Number b |
| `lang_b` | `string` | no | Lang b |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/bridge \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /bridges`

List all bridges.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/bridges
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active_bridges": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `calling_a`, `ended`, `listening`, `ok`, `translated`

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
