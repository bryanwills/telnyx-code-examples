# API Reference — Missions AI Task Runner

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/run` | Run ai task. |
| `GET` | `/runs` | List runs. |
| `GET` | `/actions` | List actions. |
| `GET` | `/health` | Health check and service status. |

---

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

---

## `GET /runs`

List all runs.

### Response `200`

```json
{
  "error": "invalid request body"
}
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
