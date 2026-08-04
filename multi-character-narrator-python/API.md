## `POST /narrate`

Render a multi-character script to a single stitched MP3.

### Request

```json
{
  "title": "Scene 1 — Coffee Shop",
  "script": "Narrator: The coffee shop buzzed.\nBob: Did you see the news?\nAlice: I did. Wild, right?",
  "voices": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | no | Project name (default: `Untitled Scene`) |
| `script` | `string` | **yes** | Multi-line script. Each line: `Speaker: text`. Lines without a label are appended to the previous speaker. Blank lines are skipped. |
| `voices` | `object` | no | Override the default speaker → voice map. Keys are speaker labels, values are `Telnyx.Ultra.<voice_uuid>` strings. Speaker labels not in the map fall back to `Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f` (Clara - Instructor). |

### Response `200`

```json
{
  "project_id": "narr-a1b2c3d4",
  "title": "Scene 1 — Coffee Shop",
  "lines_rendered": 4,
  "lines_failed": 0,
  "speakers": ["Alice", "Bob", "Carol", "Narrator"],
  "voice_map": {
    "Narrator": "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f",
    "Bob": "Telnyx.Ultra.00967b2f-88a6-4a31-8153-110a92134b9f",
    "Alice": "Telnyx.Ultra.00a77add-48d5-4ef6-8157-71e5437b282d",
    "Carol": "Telnyx.Ultra.02a924f6-bb49-4177-8fbb-52238c5056d6"
  },
  "total_ms": 1840,
  "per_line_ttfb_ms": [180, 145, 152, 167],
  "audio_url": "/audio/narr-a1b2c3d4.mp3"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | `string` | ID used to retrieve the stitched audio |
| `title` | `string` | Echoed from request |
| `lines_rendered` | `integer` | Count of lines that produced audio |
| `lines_failed` | `integer` | Count of lines that errored |
| `speakers` | `array[string]` | Distinct speaker labels found in the script |
| `voice_map` | `object` | Final speaker → voice map used (defaults + overrides) |
| `total_ms` | `integer` | Sum of per-line wall-clock time |
| `per_line_ttfb_ms` | `array[int\|null]` | Time-to-first-byte per line in milliseconds, in script order. `null` if the line errored. |
| `audio_url` | `string` | Path to stream the stitched MP3 |
| `errors` | `array[object]` | Present only when at least one line failed. Each entry has `order`, `speaker`, `error`. |

### Response `400`

```json
{"error": "Missing required field: 'script'"}
```

```json
{"error": "No speakable lines found in script"}
```

### Response `500`

```json
{"error": "TELNYX_API_KEY is not set"}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/narrate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Scene 1",
    "script": "Narrator: Hello world.\nBob: Hi there.\nAlice: Welcome."
  }'
```

---

## `GET /audio/<project_id>.mp3`

Stream the stitched MP3 for a project. Projects expire from memory after 1 hour.

### Response `200`

Binary MP3 audio with `Content-Type: audio/mpeg`.

### Response `404`

```json
{"error": "project not found"}
```

**Try it:**

```bash
curl -o scene.mp3 http://localhost:5000/audio/narr-a1b2c3d4.mp3
ffprobe scene.mp3
```

---

## `GET /projects`

List recent render projects (metadata only, no audio bytes).

### Response `200`

```json
{
  "projects": [
    {
      "id": "narr-a1b2c3d4",
      "title": "Scene 1 — Coffee Shop",
      "lines_rendered": 4,
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
