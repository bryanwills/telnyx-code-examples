## `POST /transcribe`

Upload an audio file, get a transcript back. The transcript is stored in memory and available for download as a .txt file.

### Request

Multipart form data:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | `file` | **yes** | Audio file (.webm, .mp3, .wav, .m4a, .ogg, .flac) |

### Response `200`

```json
{
  "note_id": "note-a1b2c3d4",
  "transcript": "Hello, this is a voice note taken with Telnyx Speech-to-Text.",
  "timestamp": "2026-08-05 12:34:56",
  "download_url": "/notes/note-a1b2c3d4/download"
}
```

### Response `400`

```json
{"error": "Missing required file upload: 'audio'"}
```

```json
{"error": "Audio file is empty"}
```

### Response `502`

```json
{"error": "STT failed: HTTP 400: ..."}
```

```json
{"error": "STT returned empty transcript"}
```

**Try it:**

```bash
curl -X POST http://localhost:5050/transcribe \
  -F audio=@note.webm
```

---

## `GET /notes/<note_id>/download`

Download the transcript as a .txt file. Notes expire from memory after 1 hour.

### Response `200`

Text file with `Content-Type: text/plain`, `Content-Disposition: attachment`.

### Response `404`

```json
{"error": "note not found"}
```

**Try it:**

```bash
curl -OJ http://localhost:5050/notes/note-a1b2c3d4/download
```

---

## `GET /notes`

List all transcribed notes (metadata only, no full transcript).

### Response `200`

```json
{
  "notes": [
    {
      "id": "note-a1b2c3d4",
      "transcript": "Hello, this is a voice note...",
      "created_at": 1722782400.0
    }
  ]
}
```

---

## `GET /health`

Liveness check.

### Response `200`

```json
{"status": "ok", "uptime_s": 3600}
```
