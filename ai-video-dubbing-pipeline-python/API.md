## `POST /dub`

Start dubbing.

### Response `200`

```json
{"error": "Upload an audio file as "audio""}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/dub \
  -H "Content-Type: application/json" \
  -d '{"error": "Upload an audio file as "audio""}'
```

---

## `GET /dub/<job_id>`

Get a specific job by ID.

### Response `200`

```json
{
  "error": "Upload an audio file as 'audio"
}
```

**Try it:**

```bash
curl http://localhost:5000/dub/example-id
```

---

## `GET /dub/<job_id>/transcript`

Get a specific transcript by ID.

### Response `200`

```json
{
  "error": "Job not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/dub/example-id/transcript
```

---

## `GET /languages`

List all languages.

### Response `200`

```json
{
  "error": "Job not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/languages
```

---

## `GET /jobs`

List all jobs.

### Response `200`

```json
{
  "languages": "example-value"
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
  "active": "example-value",
  "supported_languages": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `complete`, `failed`, `ok`, `synthesizing`, `transcribing`, `translating`

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
