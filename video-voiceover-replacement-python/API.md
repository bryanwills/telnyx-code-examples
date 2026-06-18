## `POST /replace`

Replace voiceover.

### Response `200`

```json
{"error": "Upload audio file as "audio""}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/replace \
  -H "Content-Type: application/json" \
  -d '{"error": "Upload audio file as "audio""}'
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

**Try it:**

```bash
curl http://localhost:5000/replace/example-id
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

**Try it:**

```bash
curl http://localhost:5000/replace/example-id/compare
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

**Try it:**

```bash
curl http://localhost:5000/modes
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
  "total_jobs": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
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
