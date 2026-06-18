## `POST /run`

Run ai task.

### Request

```json
{
  "objective": "objective-value",
  "context": {},
  "max_steps": "max-steps-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `objective` | `string` | no | Objective |
| `context` | `object` | no | Context |
| `max_steps` | `string` | no | Max steps |

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{"objective": "objective-value", "context": {}, "max_steps": "max-steps-value"}'
```

---

## `GET /runs`

List all runs.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/runs
```

---

## `GET /actions`

List all actions.

### Response `200`

```json
{
  "runs": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/actions
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "runs": "<string>"
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
  "actions": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
