# API Reference — List AI Assistants

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/assistants` | List assistants. |

---

## `GET /assistants`

List all assistants.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

---

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
