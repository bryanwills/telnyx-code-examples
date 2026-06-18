## `POST /sip/setup`

Setup sip endpoint.

### Request

```json
{
  "name": "Jane Smith",
  "username": "username-value",
  "password": "password-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `username` | `string` | **yes** | Username |
| `password` | `string` | **yes** | Password |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/sip/setup \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "username": "username-value", "password": "password-value"}'
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
