## `GET /audit/elevenlabs`

Audit elevenlabs.

### Response `200`

```json
{
  "error": "ELEVENLABS_API_KEY not configured"
}
```

**Try it:**

```bash
curl http://localhost:5000/audit/elevenlabs
```

---

## `POST /migrate/voice-config`

Migrate voice.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `elevenlabs_voice_name` | `string` | no | Elevenlabs voice name |
| `speed` | `string` | no | Speed |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/migrate/voice-config \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /mapping/voices`

Voice mapping.

### Response `200`

```json
{
  "mappings": "example-value",
  "custom_note": "For cloned/custom ElevenLabs voices"
}
```

**Try it:**

```bash
curl http://localhost:5000/mapping/voices
```

---

## `GET /cost-comparison`

Cost comparison.

### Response `200`

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

**Try it:**

```bash
curl http://localhost:5000/cost-comparison
```

---

## `POST /test-tts`

Test tts.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | no | Text content |
| `voice_id` | `string` | no | Voice id |

### Response `200`

```json
{"status": "generated", "voice": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/test-tts \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /migration-log`

Get a specific log by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/migration-log
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "migrations": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `generated`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "log": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
