## `GET /assistants`

List all assistants.

### Response `200`

```json
{
  "assistants": [
    {
      "id": "asst_abc123",
      "name": "Sales Agent",
      "model": "moonshotai/Kimi-K2.6",
      "created_at": "2026-06-18T21:00:00Z"
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/assistants
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
