## `POST /courses/create`

Create a new course.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | no | Title |
| `content` | `string` | no | Content |
| `voice` | `string` | no | TTS voice identifier |
| `include_quizzes` | `boolean` | no | Include quizzes |

### Response `200`

```json
{"error": "Provide "content" text"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/courses/create \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /courses/<course_id>`

Get a specific course by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/courses/example-id
```

---

## `GET /courses`

List all courses.

### Response `200`

```json
{
  "error": "Course not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/courses
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_courses": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `complete`, `failed`, `narrating`, `ok`, `structuring`

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
