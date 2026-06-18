## `POST /setup`

Setup bucket.

### Response `200`

```json
{
  "status": "bucket_created",
  "bucket": "example-value",
  "categories": "example-value"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/setup \
  -H "Content-Type: application/json" \
  -d '{"status": "bucket_created", "bucket": "example-value", "categories": "example-value"}'
```

---

## `POST /upload`

Upload media.

### Request

```json
{
  "category": "category-value",
  "name": "Jane Smith",
  "url": "url-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | `string` | no | Category |
| `name` | `string` | **yes** | Display name or label |
| `url` | `string` | **yes** | URL to process |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/upload \
  -H "Content-Type: application/json" \
  -d '{"category": "category-value", "name": "Jane Smith", "url": "url-value"}'
```

---

## `GET /media`

List all media.

### Response `200`

```json
{
  "media": "example-value",
  "category": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/media
```

---

## `GET /media/<category>/<name>`

Get media url.

### Response `200`

```json
{
  "url": "https://api.telnyx.com/v2/...",
  "item": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/media/example-id/example-id
```

---

## `GET /ivr-config`

Ivr config.

### Response `200`

```json
{
  "ivr_prompts": "example-value",
  "hold_music": "example-value",
  "usage": "Use these URLs in your TeXML Play or Call Control playback_audio commands"
}
```

**Try it:**

```bash
curl http://localhost:5000/ivr-config
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_media": 3,
  "bucket": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `bucket_created`, `ok`, `uploaded`

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
