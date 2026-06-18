## `POST /documents`

Add document.

### Request

```json
{
  "title": "title-value",
  "content": "content-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | no | Title |
| `content` | `string` | no | Content |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/documents \
  -H "Content-Type: application/json" \
  -d '{"title": "title-value", "content": "content-value"}'
```

---

## `POST /ask`

Ask question.

### Request

```json
{
  "documents": [],
  "total_chunks": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `string` | no | Question |
| `top_k` | `string` | no | Top k |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"documents": [], "total_chunks": "example-value"}'
```

---

## `GET /documents`

List all documents.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/documents
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "documents": "<string>",
  "chunks": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `indexed`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "documents": "example-value",
  "chunks": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
