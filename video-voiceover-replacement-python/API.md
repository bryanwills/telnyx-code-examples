# API Reference — Video Voice-Over Replacement

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/replace` | Replace voiceover. |
| `GET` | `/replace/<job_id>` | Get job. |
| `GET` | `/replace/<job_id>/compare` | Compare scripts. |
| `GET` | `/modes` | List modes. |
| `GET` | `/jobs` | List jobs. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /replace`

Replace voiceover.

### Response `200`

```json
{"error": "Upload audio file as "audio""}
```

---

## `GET /replace/<job_id>`

Get a specific job by ID.

### Response `200`

```json
{
  "error": "Upload audio file as 'audio"
}
```

---

## `GET /replace/<job_id>/compare`

Compare scripts.

### Response `200`

```json
{
  "error": "Job not found"
}
```

---

## `GET /modes`

List all modes.

### Response `200`

```json
{
  "error": "Job not found"
}
```

---

## `GET /jobs`

List all jobs.

### Response `200`

```json
{
  "modes": "example-value"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_jobs": "example-value",
  "version": "1.0.0"
}
```

---

## Status Values

Records use these status values: `complete`, `failed`, `ok`, `rendering`, `rewriting`, `transcribing`

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
