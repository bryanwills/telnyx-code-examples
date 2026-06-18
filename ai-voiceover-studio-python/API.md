## `POST /projects/create`

Create a new project.

### Request

```json
{
  "script": "script-value",
  "title": "title-value",
  "voice": "voice-value",
  "style": "style-value",
  "takes": "takes-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `script` | `string` | no | Script |
| `title` | `string` | no | Title |
| `voice` | `string` | no | TTS voice identifier |
| `style` | `string` | no | Style |
| `takes` | `string` | no | Takes |

### Response `200`

```json
{"error": "Provide "script" text"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/projects/create \
  -H "Content-Type: application/json" \
  -d '{"script": "script-value", "title": "title-value", "voice": "voice-value", "style": "style-value", "takes": "takes-value"}'
```

---

## `POST /projects/<project_id>/retake`

Retake.

### Request

```json
{
  "voice": "voice-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `voice` | `string` | no | TTS voice identifier |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/projects/example-id/retake \
  -H "Content-Type: application/json" \
  -d '{"voice": "voice-value"}'
```

---

## `GET /projects/<project_id>`

Get a specific project by ID.

### Response `200`

```json
{
  "error": "Project not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/projects/example-id
```

---

## `GET /projects`

List all projects.

### Response `200`

```json
{
  "error": "Project not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/projects
```

---

## `GET /voices`

List all voices.

### Response `200`

```json
{"voices": {k: v["desc"] for k, v in VOICES."<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/voices
```

---

## `GET /styles`

List all styles.

### Response `200`

```json
{"styles": STYLES}
```

**Try it:**

```bash
curl http://localhost:5000/styles
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "styles": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `complete`, `directing`, `failed`, `ok`, `rendering`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "total_projects": "example-value",
  "bucket": "example-value",
  "version": "1.0.0"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
