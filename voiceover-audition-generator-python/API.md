## `POST /auditions/create`

Create a new audition.

### Request

```json
{
  "script": "script-value",
  "project": "project-value",
  "context": "context-value",
  "notify": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `script` | `string` | no | Script |
| `project` | `string` | no | Project |
| `context` | `string` | no | Context |
| `notify` | `array` | no | Notify |

### Response `200`

```json
{"error": "Provide "script" text"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/auditions/create \
  -H "Content-Type: application/json" \
  -d '{"script": "script-value", "project": "project-value", "context": "context-value", "notify": []}'
```

---

## `GET /auditions/<audition_id>`

Get a specific audition by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/auditions/example-id
```

---

## `GET /auditions`

List all auditions.

### Response `200`

```json
{
  "error": "Audition not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/auditions
```

---

## `GET /voices`

List all voices.

### Response `200`

```json
{
  "voices": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/voices
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_auditions": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `complete`, `ok`, `rendering`, `scoring`

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
