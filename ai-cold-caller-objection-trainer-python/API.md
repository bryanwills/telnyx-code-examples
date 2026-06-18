## `POST /train`

Start training.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rep_number` | `string` | **yes** | Rep number |
| `persona` | `number` | no | Persona |

### Response `200`

```json
{"status": "calling", "persona": persona["name"]}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/train \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /results`

Get a specific results by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/results
```

---

## `GET /personas`

List all personas.

### Response `200`

```json
{"personas": [{"index": null, "name": p["name"], "style": p["style"]}
```

**Try it:**

```bash
curl http://localhost:5000/personas
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active": "<string>",
  "completed": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `calling`, `ended`, `in_character`, `listening`, `ok`, `reprompting`, `responding`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
