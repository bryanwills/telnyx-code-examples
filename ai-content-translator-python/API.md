## `POST /translate`

Translate content.

### Response `200`

```json
{"error": "Upload audio file as "audio""}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{"error": "Upload audio file as "audio""}'
```

---

## `GET /translate/<job_id>`

Get a specific translation by ID.

### Response `200`

```json
{
  "error": "Upload audio file as 'audio"
}
```

**Try it:**

```bash
curl http://localhost:5000/translate/example-id
```

---

## `GET /languages`

List all languages.

### Response `200`

```json
{"languages": {k: v["name"] for k, v in LANGUAGES."<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/languages
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "Job not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `complete`, `failed`, `ok`, `partial`, `processing`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "total_translations": "example-value",
  "supported_languages": "example-value",
  "version": "1.0.0"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
