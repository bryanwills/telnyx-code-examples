## `POST /inference/chat`

Chat endpoint.

### Request

```json
{
  "error": "Request body must include 'messages' array"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | `string` | **yes** | AI model name |
| `max_tokens` | `number` | no | Maximum tokens for AI response |
| `temperature` | `string` | no | Temperature |

### Response `200`

```json
{"error": "Request body must include "messages" array"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/inference/chat \
  -H "Content-Type: application/json" \
  -d '{"error": "Request body must include 'messages' array"}'
```

---

## `POST /inference/ask`

Ask endpoint.

### Request

```json
{
  "error": "Request body must include 'messages' array"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `system_prompt` | `string` | **yes** | System prompt |

### Response `200`

```json
{"error": "Request body must include "question""}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/inference/ask \
  -H "Content-Type: application/json" \
  -d '{"error": "Request body must include 'messages' array"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "Request body must include 'question"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "model": "moonshotai/Kimi-K2.6"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
