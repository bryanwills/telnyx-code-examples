## `POST /transcribe`

Upload an audio file for transcription via Telnyx STT.

### Request

Multipart form data:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | `file` | **yes** | Audio file (.webm, .mp3, .wav, .m4a, .ogg, .flac). Max 25 MB. |

### Response `200`

```json
{
  "note_id": "note-a1b2c3d4",
  "transcript": "Welcome to the Telnyx developer platform.",
  "detected_language": "English",
  "model": "openai/whisper-large-v3-turbo",
  "duration_ms": 1234,
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

```json
{"error": "Unsupported file format: .xyz. Supported: .flac, .m4a, .mp3, .ogg, .wav, .webm"}
```

### Response `413`

```json
{"error": "Audio file exceeds 25 MB limit"}
```

### Response `502`

```json
{"error": "STT failed: HTTP 401: ..."}
```

```json
{"error": "STT returned empty transcript"}
```

**Try it:**

```bash
curl -X POST http://localhost:5050/transcribe -F audio=@note.webm
```

---

## `POST /translate`

Translate text via Telnyx Inference (OpenAI-compatible chat completions).

### Request

```json
{
  "source_text": "Welcome to the Telnyx developer platform.",
  "target_language": "Spanish"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_text` | `string` | **yes** | Text to translate. Max 10,000 characters. |
| `target_language` | `string` | **yes** | One of: Spanish, English, French, German, Italian, Portuguese, Hindi, Japanese. |

### Response `200`

```json
{
  "translation_id": "trans-a1b2c3d4",
  "source_text": "Welcome to the Telnyx developer platform.",
  "target_language": "Spanish",
  "translated_text": "Bienvenido a la plataforma para desarrolladores de Telnyx.",
  "download_url": "/notes/trans-a1b2c3d4/download"
}
```

### Response `400`

```json
{"error": "Missing required field: 'source_text'"}
```

```json
{"error": "Unsupported target language: Korean. Supported: Spanish, English, French, German, Italian, Portuguese, Hindi, Japanese"}
```

### Response `413`

```json
{"error": "Source text exceeds 10000 character limit"}
```

**Try it:**

```bash
curl -X POST http://localhost:5050/translate \
  -H "Content-Type: application/json" \
  -d '{"source_text":"Hello world","target_language":"Spanish"}'
```

---

## `POST /synthesize`

Generate speech from translated text via Telnyx TTS.

### Request

```json
{
  "text": "Bienvenido a la plataforma para desarrolladores de Telnyx.",
  "target_language": "Spanish"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | **yes** | Text to synthesize. Max 3,000 characters. |
| `target_language` | `string` | **yes** | Target language for `voice_settings.language_boost`. |

### Response `200`

```json
{
  "audio_id": "audio-a1b2c3d4",
  "target_language": "Spanish",
  "voice": "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f",
  "audio_url": "/audio/audio-a1b2c3d4",
  "download_url": "/audio/audio-a1b2c3d4/download"
}
```

### Response `400`

```json
{"error": "Missing required field: 'text'"}
```

### Response `413`

```json
{"error": "Text exceeds 3000 character limit for TTS"}
```

**Try it:**

```bash
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hola mundo","target_language":"Spanish"}'
```

---

## `GET /audio/<audio_id>`

Stream generated audio.

### Response `200`

Binary audio with `Content-Type: audio/mp3`.

### Response `404`

```json
{"error": "audio not found"}
```

---

## `GET /audio/<audio_id>/download`

Download generated audio as a file.

### Response `200`

Audio file with `Content-Disposition: attachment`. Filename format: `{language}-audio-{date}.mp3`.

---

## `GET /notes/<note_id>/download`

Download a transcript or translation as a .txt file.

### Response `200`

Text file with `Content-Disposition: attachment`. Filename format:
- Original: `original-transcript-{date}.txt`
- Translation: `{language}-translation-{date}.txt`

### Response `404`

```json
{"error": "note not found"}
```

---

## `GET /health`

Liveness check with configured model info.

### Response `200`

```json
{
  "status": "ok",
  "uptime_s": 3600,
  "stt_model": "openai/whisper-large-v3-turbo",
  "translation_model": "moonshotai/Kimi-K2.6",
  "tts_voice": "Telnyx.Ultra.01eaafa9-...",
  "target_languages": ["Spanish", "English", "French", "German", "Italian", "Portuguese", "Hindi", "Japanese"]
}
```
