# API Reference — Bulk Number Validation & Cleaner

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/validate` | Validate numbers. |
| `GET` | `/validate/single/<number>` | Validate single. |
| `GET` | `/jobs` | List jobs. |
| `GET` | `/health` | Health check and service status. |

---

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

---

## `GET /validate/single/<number>`

Validate single.

### Response `200`

```json
{
  "error": "Error description"
}
```

---

## `GET /jobs`

List all jobs.

### Response `200`

```json
{"jobs": null}
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
