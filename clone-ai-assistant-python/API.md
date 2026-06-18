## `GET /assistants/<assistant_id>`

Get a specific assistant by ID.

### Response `200`

```json
{
  "error": "assistant_id is required"
}
```

**Try it:**

```bash
curl http://localhost:5000/assistants/example-id
```

---

## `POST /assistants/<assistant_id>/clone`

Clone assistant endpoint.

### Request

```json
{
  "name": "Jane Smith",
  "instructions": "instructions-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `instructions` | `string` | **yes** | Instructions |

### Response `200`

```json
{
  "error": "assistant_id is required"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/assistants/example-id/clone \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "instructions": "instructions-value"}'
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
