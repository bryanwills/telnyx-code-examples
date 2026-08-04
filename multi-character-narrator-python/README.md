---
name: multi-character-narrator
title: "Multi-Character Narrator"
description: "Paste a dialogue script with speaker labels, assign each speaker a distinct Telnyx Ultra voice, render every line in parallel, and stitch the per-line audio into one continuous MP3."
language: python
framework: flask
telnyx_products: [Text-to-Speech]
channel: [api]
---

# Multi-Character Narrator

Paste a dialogue script with speaker labels (e.g. `Narrator:`, `Bob:`, `Alice:`, `Carol:`), assign each speaker a distinct Telnyx Ultra voice, render every line in parallel, and stitch the per-line audio into one continuous MP3. Pure TTS, no phone, no webhook, no Cloud Storage required.

## Telnyx API Endpoints Used

- **Text-to-Speech (Ultra, REST)**: `POST /v2/text-to-speech/speech` — [API reference](https://developers.telnyx.com/api/inference/generate-speech-from-text)
  - Voice format: `Telnyx.Ultra.<voice_uuid>` — Ultra voice IDs are UUIDs, not short names. Enumerate available voices with `GET /v2/text-to-speech/voices`.
  - Ultra is **REST-only** — a 403 on `wss://` is intentional. Use this REST endpoint, not the public WebSocket.
  - `output_type: "binary_output"` is used so we can measure true time-to-first-byte per line.

> Note: Other TTS examples in this repo use the OpenAI-compatible `/v2/ai/generate` endpoint. This example uses the full Telnyx TTS endpoint `/v2/text-to-speech/speech` because Ultra voices are exposed there. Both endpoints accept a Bearer API key.

## Architecture

```
  POST /narrate  (script with speaker labels)
        │
        ▼
  ┌──────────────────────┐
  │ Parse script         │  → lines = [{speaker, text, order}, ...]
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────────────┐
  │ Map speaker → voice  │  (4 pre-built Telnyx Ultra voices, overridable)
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────────────┐
  │ Parallel TTS fan-out │  ThreadPoolExecutor, one POST per line
  │ N Ultra REST calls   │  measure TTFB per line (binary_output stream)
  └────────┬─────────────┘
           │
           ▼
  ┌──────────────────────┐
  │ Stitch audio bytes   │  concatenate MP3 frames in script order
  └────────┬─────────────┘
           │
           ▼
  Return: project_id, total_ms, per_line_ttfb_ms, audio_url
```

## How It Works

1. The caller POSTs a multi-line script. Each line is `Speaker: text`. Lines without a label inherit the previous speaker.
2. The Flask app maps each speaker label to one of four pre-built Telnyx Ultra voices (`Telnyx.Ultra.Clara`, `Telnyx.Ultra.Asher`, `Telnyx.Ultra.Callie`, plus a fallback). The caller can override the map per request.
3. The app fans out one REST TTS call per line in parallel (up to 8 concurrent), streaming the binary response so it can measure true time-to-first-byte for each line.
4. Successful audio chunks are concatenated in original script order to produce one continuous MP3.
5. The result is stored in memory (1-hour TTL) and served via `/audio/<project_id>.mp3`.

## Why Telnyx

Telnyx AI Communications Infrastructure ships sub-100ms TTFB Text-to-Speech on the Ultra provider with one voice platform covering 36 languages. Multi-character narration — audiobook chapters with dialogue, podcasts with multiple hosts, e-learning role-plays, game cinematics — is usually stitched together in a DAW across multiple vendors. With Telnyx, one API key, one endpoint, and four pre-built Ultra voices produce a finished scene in a single request.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) · [CLI: `telnyx auth`](https://developers.telnyx.com/development/cli) |

No phone number, connection ID, public key, or webhook URL is required — this example is pure TTS.

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/multi-character-narrator-python
cp .env.example .env    # ← fill in your TELNYX_API_KEY
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

<details>
<summary>Programmatic / CLI setup</summary>

```bash
# Install CLI — https://developers.telnyx.com/development/cli
go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest
telnyx auth login
```

To enumerate available Ultra voices before overriding the default map:

```bash
curl -H "Authorization: Bearer $TELNYX_API_KEY" \
  https://api.telnyx.com/v2/text-to-speech/voices | jq '.voices[] | select(.id | startswith("Telnyx.Ultra."))'
```

For full API discovery, point your agent at [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt).

</details>

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/multi-character-narrator-python/API.md) for the full typed endpoint reference. Quick start:

```bash
curl -X POST http://localhost:5000/narrate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Scene 1 — Coffee Shop",
    "script": "Narrator: The coffee shop buzzed with morning chatter.\nBob: Did you see the news?\nAlice: I did. Wild, right?\nCarol: We should talk about it."
  }'
```

Response:

```json
{
  "project_id": "narr-a1b2c3d4",
  "title": "Scene 1 — Coffee Shop",
  "lines_rendered": 4,
  "lines_failed": 0,
  "speakers": ["Alice", "Bob", "Carol", "Narrator"],
  "voice_map": {
    "Narrator": "Telnyx.Ultra.Clara",
    "Bob": "Telnyx.Ultra.Asher",
    "Alice": "Telnyx.Ultra.Callie",
    "Carol": "Telnyx.Ultra.Clara"
  },
  "total_ms": 1840,
  "per_line_ttfb_ms": [180, 145, 152, 167],
  "audio_url": "/audio/narr-a1b2c3d4.mp3"
}
```

Stream the stitched audio:

```bash
curl -o scene.mp3 http://localhost:5000/audio/narr-a1b2c3d4.mp3
ffprobe scene.mp3   # should report MP3, ~seconds long
```

## Default Voice Map

| Speaker label | Voice | Display name | Gender | Language |
|---|---|---|---|---|
| `Narrator` | `Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f` | Clara - Instructor | Female | en-US |
| `Bob` | `Telnyx.Ultra.00967b2f-88a6-4a31-8153-110a92134b9f` | Asher - Podcaster | Male | en-US |
| `Alice` | `Telnyx.Ultra.00a77add-48d5-4ef6-8157-71e5437b282d` | Callie - Encourager | Female | en-US |
| `Carol` | `Telnyx.Ultra.02a924f6-bb49-4177-8fbb-52238c5056d6` | Maeve - Steady Host | Female | en-US |

Override per request by passing a `voices` object in the JSON body. Speaker labels not present in the map fall back to `Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f` (Clara - Instructor).

To enumerate every available Ultra voice and pick your own:

```bash
curl -H "Authorization: Bearer $TELNYX_API_KEY" \
  https://api.telnyx.com/v2/text-to-speech/voices \
  | jq '.voices[] | select(.provider == "telnyx" and (.id | startswith("Telnyx.Ultra.")))'
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` from `/narrate` | Missing or invalid `TELNYX_API_KEY` | Set `TELNYX_API_KEY` in `.env` from the [Portal](https://portal.telnyx.com/api-keys) |
| `403 Forbidden` from a `wss://` URL | Ultra is REST-only on the public WebSocket | Use `POST /v2/text-to-speech/speech`, not the WebSocket endpoint |
| `400` with `invalid voice specification` | Voice string is not in `Telnyx.Ultra.<uuid>` form | Ultra voice IDs are UUIDs, not display names. Enumerate valid voices with `GET /v2/text-to-speech/voices` |
| `429 Too Many Requests` | Hit TTS rate limit during parallel fan-out | Lower `MAX_WORKERS` in `app.py` or retry with exponential backoff |
| Stitched MP3 plays only the first line | Bytes from one line are zero-length | Check the `errors` array in the response — failed lines are skipped, not silent |
| Two characters sound identical | Both speaker labels mapped to the same Ultra voice UUID | Override via the `voices` field, or pick distinct UUIDs from `GET /v2/text-to-speech/voices` |
| Long scripts (>50 lines) timeout | Default `max_workers=8` plus 60s per-line timeout | Split the script, or increase `MAX_WORKERS` and the per-request timeout |

## Related Examples

- [`ai-voiceover-studio-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-voiceover-studio-python) — single-voice voice-over with AI direction cues
- [`ai-audiobook-narrator-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-audiobook-narrator-python) — single-voice long-form narration with chapter chunking
- [`multilingual-voiceover-kit-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/multilingual-voiceover-kit-python) — same script rendered in 15 languages
- [`commercial-voiceover-generator-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/commercial-voiceover-generator-python) — 3 AI-written script variations rendered in multiple voices
- [`text-to-speech-phone-call-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/text-to-speech-phone-call-python) — TTS playback during a live phone call

## Agent Discovery

This example is part of the [Telnyx Code Examples](https://github.com/team-telnyx/telnyx-code-examples) catalog.

- **Agent signup**: [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md) — automated account provisioning via agent mail; get an API key with no human intervention
- **Agent CLI**: [github.com/team-telnyx/ai/tree/main/cli](https://github.com/team-telnyx/ai/tree/main/cli) — composite commands for agents ([commands reference](https://github.com/team-telnyx/ai/tree/main/cli/src/commands))
- **Agent skills**: [github.com/team-telnyx/ai/tree/main/skills](https://github.com/team-telnyx/ai/tree/main/skills)
- **Telnyx AI repo**: [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLM-optimized docs**: [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt)
- **Example index**: [`llms.txt`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/llms.txt)
- **Telnyx CLI (human)**: [developers.telnyx.com/development/cli](https://developers.telnyx.com/development/cli) — `go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest`

## Resources

- TTS overview: [developers.telnyx.com/docs/voice/tts](https://developers.telnyx.com/docs/voice/tts)
- Ultra provider docs (voices, REST fields, SSML emotions): [developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra](https://developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra)
- TTS REST request reference: [developers.telnyx.com/docs/voice/tts/rest-api/request](https://developers.telnyx.com/docs/voice/tts/rest-api/request)
- Voices API: [GET /v2/text-to-speech/voices](https://api.telnyx.com/v2/text-to-speech/voices) — enumerate every available TTS voice (AWS, Azure, Telnyx Natural/NaturalHD/Ultra, etc.)
- Repo CONTRIBUTING.md: [github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md](https://github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md)
