## `POST /clip`

Clip highlights.

### Response `200`

```json
{"error": "Upload audio as "audio""}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/clip \
  -H "Content-Type: application/json" \
  -d '{"error": "Upload audio as "audio""}'
```

---

## `GET /clip/<job_id>`

Get a specific job by ID.

### Response `200`

```json
{
  "error": "Upload audio as 'audio"
}
```

**Try it:**

```bash
curl http://localhost:5000/clip/example-id
```

---

## `POST /distribution`

Add to distribution.

### Request

```json
{
  "phone": "+12125559999"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |

### Response `200`

```json
{
  "total": "<string>"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/distribution \
  -H "Content-Type: application/json" \
  -d '{"phone": "+12125559999"}'
```

---

## `GET /jobs`

List all jobs.

### Response `200`

```json
{
  "error": "Job not found"
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
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `analyzing`, `complete`, `failed`, `generating_teasers`, `ok`, `transcribing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "total_jobs": "example-value",
  "version": "1.0.0"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
