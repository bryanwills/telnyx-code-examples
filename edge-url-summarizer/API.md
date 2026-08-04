## `POST /summarize`

Summarize a URL. First call hits the model, repeat calls return from cache.

### Request

```json
{
  "url": "https://example.com/article"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | `string` | **yes** | The URL to summarize |

### Response `201` (cache miss)

```json
{
  "url": "https://example.com/article",
  "title": "Example Article",
  "bullets": ["point 1", "point 2", "point 3"],
  "word_count": 1234,
  "generated_at": "2026-08-04T12:00:00Z",
  "cached": false
}
```

### Response `200` (cache hit — no model call)

```json
{
  "url": "https://example.com/article",
  "bullets": ["point 1", "point 2", "point 3"],
  "title": "Example Article",
  "word_count": 1234,
  "generated_at": "2026-08-04T12:00:00Z",
  "cached": true
}
```

**Try it:**

```bash
curl -X POST https://edge-url-summarizer-<id>.telnyxcompute.com/summarize \
  -H "Content-Type: application/json" \
  -d '{"url":"https://telnyx.com/blog"}'
```

---

## `GET /summarize/cached`

Get a cached summary by URL (no model call).

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | `string` | **yes** | The URL to look up |

### Response `200`

```json
{
  "url": "https://example.com/article",
  "bullets": ["..."],
  "cached": true
}
```

### Response `404`

```json
{"error": "not cached"}
```

**Try it:**

```bash
curl "https://edge-url-summarizer-<id>.telnyxcompute.com/summarize/cached?url=https://telnyx.com/blog"
```

---

## `POST /summarize/refresh`

Invalidate cache for a URL and re-summarize on next request.

### Request

```json
{
  "url": "https://example.com/article"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | `string` | **yes** | The URL to invalidate |

### Response `200`

```json
{
  "url": "https://example.com/article",
  "invalidated": true
}
```

**Try it:**

```bash
curl -X POST https://edge-url-summarizer-<id>.telnyxcompute.com/summarize/refresh \
  -H "Content-Type: application/json" \
  -d '{"url":"https://telnyx.com/blog"}'
```

---

## `GET /stats`

Cache hit/miss statistics.

### Response `200`

```json
{
  "total_requests": 10,
  "cache_hits": 6,
  "cache_misses": 4,
  "unique_urls": 4,
  "top_urls": ["https://example.com/1", "https://example.com/2"]
}
```

**Try it:**

```bash
curl https://edge-url-summarizer-<id>.telnyxcompute.com/stats
```

---

## `GET /cached`

List all cached URLs.

### Response `200`

```json
{
  "urls": [
    "https://example.com/1",
    "https://example.com/2"
  ]
}
```

**Try it:**

```bash
curl https://edge-url-summarizer-<id>.telnyxcompute.com/cached
```

---

## `GET /health/{liveness,readiness}`

Health check endpoints.

### Response `200`

```
ok
```

**Try it:**

```bash
curl https://edge-url-summarizer-<id>.telnyxcompute.com/health/liveness
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Summary created (cache miss) |
| `400` | Bad request — missing URL |
| `404` | Not cached or unknown route |
| `500` | Server error (fetch or inference failed) |
