## `POST /repurpose`

Repurpose episode.

### Response `200`

```json
{"error": "Upload episode audio as "audio""}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/repurpose \
  -H "Content-Type: application/json" \
  -d '{"error": "Upload episode audio as "audio""}'
```

---

## `GET /repurpose/<job_id>`

Get a specific job by ID.

### Response `200`

```json
{
  "error": "Upload episode audio as 'audio"
}
```

**Try it:**

```bash
curl http://localhost:5000/repurpose/example-id
```

---

## `POST /subscribers`

Add subscriber.

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
{"error": "Provide "phone" in E.164 format"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/subscribers \
  -H "Content-Type: application/json" \
  -d '{"phone": "+12125559999"}'
```

---

## `GET /subscribers`

List all subscribers.

### Response `200`

```json
{"subscribers": [s[-4:] for s in subscribers], "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/subscribers
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

Records use these status values: `complete`, `extracting`, `failed`, `generating_clips`, `ok`, `transcribing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "subscribers": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
