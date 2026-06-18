## `POST /kits/create`

Create a new kit.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `script` | `string` | no | Script |
| `source_language` | `string` | no | Source language |
| `target_languages` | `string` | no | Target languages |
| `project` | `string` | no | Project |
| `style` | `string` | no | Style |

### Response `200`

```json
{"error": "Provide "script" text"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/kits/create \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /kits/<kit_id>`

Get a specific kit by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/kits/example-id
```

---

## `POST /kits/<kit_id>/add-language`

Add language.

### Request

```json
{
  "language": "language-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `language` | `string` | **yes** | Language code (e.g., `en-US`) |

### Response `200`

```json
{
  "error": "Kit not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/kits/example-id/add-language \
  -H "Content-Type: application/json" \
  -d '{"language": "language-value"}'
```

---

## `GET /kits`

List all kits.

### Response `200`

```json
{
  "error": "Kit not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/kits
```

---

## `GET /languages`

List all languages.

### Response `200`

```json
{
  "languagess": [
    {
      "id": "abc-123",
      "status": "active",
      "created_at": "2026-06-18T21:00:00Z"
    }
  ],
  "total": 1
}
```

**Try it:**

```bash
curl http://localhost:5000/languages
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_kits": "example-value",
  "supported_languages": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `complete`, `ok`, `pending`, `translated`, `translating`, `translation_failed`, `tts_failed`

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
