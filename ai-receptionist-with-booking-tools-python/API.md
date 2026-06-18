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
{"response": msg["content"], "bookings": "<string>"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": []}'
```

---

## `GET /bookings`

List all bookings.

### Response `200`

```json
{"bookings": null}
```

**Try it:**

```bash
curl http://localhost:5000/bookings
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "invalid request body"
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
  "bookings": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
