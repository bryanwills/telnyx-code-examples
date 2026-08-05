## `GET /decks`

List all available flashcard decks.

### Response `200`

```json
{"decks": ["Spanish — Greetings", "Spanish — Numbers", "Spanish — Common phrases", "French — Greetings"]}
```

---

## `GET /deck/<deck_name>`

Get the cards in a specific deck.

### Response `200`

```json
{
  "name": "Spanish — Greetings",
  "language": "Spanish",
  "cards": [
    {"phrase": "Hola, como estas?", "translation": "Hello, how are you?"},
    {"phrase": "Buenos dias", "translation": "Good morning"}
  ]
}
```

### Response `404`

```json
{"error": "deck not found"}
```

---

## `POST /speak`

Generate speech for a flashcard phrase via Telnyx TTS.

### Request

```json
{"text": "Hola, como estas?", "language": "Spanish"}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | **yes** | Phrase to speak |
| `language` | `string` | **yes** | Language for `voice_settings.language_boost` |

### Response `200`

```json
{"audio_id": "audio-a1b2c3d4", "audio_url": "/audio/audio-a1b2c3d4"}
```

### Response `400`

```json
{"error": "Missing required field: 'text'"}
```

---

## `POST /check`

Upload your recording and get a pronunciation score.

### Request

Multipart form data:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | `file` | **yes** | Your recording (.webm, .mp3, etc.) |
| `target_phrase` | `string` | **yes** | The phrase you were asked to repeat |
| `language` | `string` | **yes** | Language of the phrase |

### Response `200`

```json
{
  "target_phrase": "Hola, como estas?",
  "spoken_text": "Hola, como estas?",
  "language": "Spanish",
  "score": "correct",
  "feedback": "Perfect pronunciation!"
}
```

Score values: `correct`, `close`, `wrong`.

### Response `400`

```json
{"error": "Missing required file upload: 'audio'"}
```

```json
{"error": "Missing required field: 'target_phrase'"}
```

### Response `502`

```json
{"error": "STT failed"}
```

```json
{"error": "Inference returned invalid response"}
```

---

## `GET /audio/<audio_id>`

Stream generated TTS audio.

### Response `200`

Binary audio with `Content-Type: audio/mp3`.

### Response `404`

```json
{"error": "audio not found"}
```

---

## `GET /health`

Liveness check.

### Response `200`

```json
{
  "status": "ok",
  "uptime_s": 3600,
  "stt_model": "openai/whisper-large-v3-turbo",
  "inference_model": "moonshotai/Kimi-K2.6",
  "tts_voice": "Telnyx.Ultra.01eaafa9-...",
  "decks": ["Spanish — Greetings", "Spanish — Numbers", "Spanish — Common phrases", "French — Greetings"]
}
```
