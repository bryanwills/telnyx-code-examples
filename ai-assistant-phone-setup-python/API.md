## `POST /assistants`

Create a new assistant.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | no | Display name or label |
| `instructions` | `string` | no | Instructions |
| `model` | `string` | no | AI model name |
| `voice_provider` | `string` | no | Voice provider |
| `voice_id` | `string` | no | Voice id |
| `speed` | `string` | no | Speed |
| `greeting` | `string` | no | Greeting |
| `hold_music_url` | `string` | **yes** | Hold music url |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/assistants \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `GET /assistants`

List all assistants.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/assistants
```

---

## `GET /assistants/<assistant_id>`

Get a specific assistant by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/assistants/example-id
```

---

## `PATCH /assistants/<assistant_id>`

Update assistant.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X PATCH http://localhost:5000/assistants/example-id \
  -H "Content-Type: application/json" \
  -d '{"error": "Error description"}'
```

---

## `POST /assistants/<assistant_id>/wire`

Wire to number.

### Request

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | Phone number |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/assistants/example-id/wire \
  -H "Content-Type: application/json" \
  -d '{"id": "abc-123", "status": "active", "created_at": "2026-06-18T21:00:00Z"}'
```

---

## `POST /assistants/<assistant_id>/test`

Test assistant.

### Request

```json
{
  "message": "Hello from the API"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | no | Message content to send |

### Response `200`

```json
{"response": resp."<string>".get("choices", [{}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/assistants/example-id/test \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from the API"}'
```

---

## `GET /models`

List all models.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/models
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "assistants": "<string>"
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
  "error": "Error description"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
