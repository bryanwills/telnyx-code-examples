## `POST /redact`

Redact PII from a text transcript directly.

### Request

```json
{
  "transcript": "Hi, this is John Smith. My card is 4532-1234-5678-9012."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | `string` | **yes** | The transcript text to redact (max 6000 chars) |

### Response `201`

```json
{
  "id": "red-1750280400",
  "original_transcript": "Hi, this is John Smith...",
  "redacted_transcript": "Hi, this is [NAME]...",
  "redactions": [
    {"type": "name", "original": "John Smith", "redacted": "[NAME]", "count": 1}
  ],
  "items_redacted": 1,
  "pii_types_found": ["name"],
  "source": "text",
  "status": "done",
  "generated_at": "2026-07-29T11:21:15Z"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/redact \
  -H "Content-Type: application/json" \
  -d '{"transcript":"My name is Jane Doe and my email is jane@doe.com"}'
```

---

## `POST /redact/audio`

Upload an audio file → transcribe via STT → redact PII.

### Request (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `file` | **yes** | Audio file (WAV, MP3, etc.) |
| `language` | `string` | no | Language hint (e.g. `en-US`, `es-US`). Not all STT models support this. |

### Response `201`

```json
{
  "id": "red-1750280401",
  "original_transcript": "Hello, this is Sarah Johnson...",
  "redacted_transcript": "Hello, this is [NAME]...",
  "redactions": [...],
  "items_redacted": 1,
  "source": "audio:recording.wav",
  "status": "done",
  "generated_at": "2026-07-29T11:24:18Z"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/redact/audio \
  -F "file=@recording.wav"
```

---

## `GET /redactions`

List recent redaction jobs (most recent 50).

### Response `200`

```json
{
  "redactions": [
    {
      "id": "red-1750280400",
      "source": "text",
      "items_redacted": 3,
      "pii_types_found": ["name", "credit_card"],
      "status": "done",
      "generated_at": "2026-07-29T11:21:15Z"
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/redactions
```

---

## `GET /redactions/<id>`

Fetch a specific redaction result.

### Response `200`

```json
{
  "id": "red-1750280400",
  "original_transcript": "...",
  "redacted_transcript": "...",
  "redactions": [...],
  "items_redacted": 3
}
```

### Response `404`

```json
{"error": "redaction not found"}
```

**Try it:**

```bash
curl http://localhost:5000/redactions/red-1750280400
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "redactions": 0,
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Redaction created |
| `400` | Bad request — missing file or transcript |
| `404` | Redaction not found |
| `422` | Transcription returned empty text |
| `500` | Server error |
