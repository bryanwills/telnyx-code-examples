## `POST /books/narrate`

Narrate book.

### Request

```json
{
  "title": "title-value",
  "text": "Hello from the API",
  "voice": "voice-value",
  "author": "author-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | no | Title |
| `text` | `string` | no | Text content |
| `voice` | `string` | no | TTS voice identifier |
| `author` | `string` | no | Author |

### Response `200`

```json
{"error": "Provide "text" to narrate"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/books/narrate \
  -H "Content-Type: application/json" \
  -d '{"title": "title-value", "text": "Hello from the API", "voice": "voice-value", "author": "author-value"}'
```

---

## `GET /books/<book_id>`

Get a specific book by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/books/example-id
```

---

## `GET /books`

List all books.

### Response `200`

```json
{
  "error": "Book not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/books
```

---

## `GET /voices`

List all voices.

### Response `200`

```json
{
  "voices": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/voices
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_books": "example-value",
  "bucket": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `chunking`, `complete`, `failed`, `narrating`, `ok`

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
