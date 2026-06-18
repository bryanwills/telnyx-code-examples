## `POST /chat`

Chat.

### Request

```json
{
  "messages": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | `array` | no | Messages |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": []}'
```

---

## `GET /tools`

List all tools.

### Response `200`

```json
{"tools": TOOLS}
```

**Try it:**

```bash
curl http://localhost:5000/tools
```

---

## `GET /tool-calls`

List tool calls.

### Response `200`

```json
{
  "tools": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/tool-calls
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "tools": "<string>",
  "calls": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `booked`, `ok`, `processing`, `shipped`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "calls": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
