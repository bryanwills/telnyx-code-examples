# Build a Multi-Character Narrator with Telnyx Ultra TTS

Paste a dialogue script with speaker labels, assign each speaker a distinct Telnyx Ultra voice, render every line in parallel, and stitch the per-line audio into one continuous MP3. Pure TTS, no phone, no webhook, no Cloud Storage.

## How It Works

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

## Telnyx Products Used

- **Text-to-Speech (Ultra)** — sub-100ms TTFB, 36 languages, REST-only on the public WebSocket. The Ultra provider exposes pre-built voices in the `Telnyx.Ultra.<voice_id>` format. This example uses four of them in parallel and stitches the result.

## API Endpoints

- **Text-to-Speech (Ultra, REST)**: `POST /v2/text-to-speech/speech` — [API reference](https://developers.telnyx.com/api/inference/generate-speech-from-text)
- **Voices API** (optional, for enumerating available Ultra voices): `GET /v2/text-to-speech/voices` — returns all voices across providers; filter to `provider == "telnyx"` and `id | startswith("Telnyx.Ultra.")` for Ultra only. Voice IDs are UUIDs (e.g. `Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f`).

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- A Telnyx API v2 key from the [Portal](https://portal.telnyx.com/api-keys)

No phone number, TeXML application, or webhook endpoint is required.

## Step 1 — Configure environment

```bash
cp .env.example .env
# Edit .env and set TELNYX_API_KEY
```

## Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

## Step 3 — Run the app

```bash
python app.py
# * Running on http://127.0.0.1:5000
```

## Step 4 — Render a scene

```bash
curl -X POST http://localhost:5000/narrate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Scene 1 — Coffee Shop",
    "script": "Narrator: The coffee shop buzzed with morning chatter.\nBob: Did you see the news?\nAlice: I did. Wild, right?\nCarol: We should talk about it."
  }'
```

The response includes `per_line_ttfb_ms` so you can see the per-line time-to-first-byte of each Ultra REST call. Successful lines are stitched in script order.

## Step 5 — Stream the audio

```bash
curl -o scene.mp3 http://localhost:5000/audio/<project_id>.mp3
afplay scene.mp3   # or open scene.mp3
```

## Step 6 — Override the default voice map

The default map assigns four pre-built Ultra voices to four common speaker labels. Override per request:

```bash
curl -X POST http://localhost:5000/narrate \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Narrator: Hello.\nDragon: Roar!\nKnight: Have at thee!",
    "voices": {
      "Narrator": "Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f",
      "Dragon": "Telnyx.Ultra.00967b2f-88a6-4a31-8153-110a92134b9f",
      "Knight": "Telnyx.Ultra.00a77add-48d5-4ef6-8157-71e5437b282d"
    }
  }'
```

To discover additional Ultra voices:

```bash
curl -H "Authorization: Bearer $TELNYX_API_KEY" \
  https://api.telnyx.com/v2/text-to-speech/voices \
  | jq '.voices[] | select(.provider == "telnyx" and (.id | startswith("Telnyx.Ultra.")))'
```

Ultra voice IDs are UUIDs (e.g. `Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f` for "Clara - Instructor"), not short display names. The voices API returns all 4,000+ voices across providers — filter on `provider == "telnyx"` and `id | startswith("Telnyx.Ultra.")` to see only Telnyx Ultra voices.

## Notes and caveats

- **Ultra is REST-only.** A 403 on `wss://api.telnyx.com/v2/text-to-speech/speech` is intentional. Use the REST endpoint.
- **MP3 stitching is byte-wise.** Per-line MP3 frames from Ultra share a format, so concatenation produces a valid MP3. For mixed providers or sample rates, re-encode with `ffmpeg` before stitching.
- **Concurrency is capped at 8.** Scripts with more than 8 lines are queued through the pool. Raise `MAX_WORKERS` in `app.py` if you need more parallelism and your TTS quota allows it.
- **In-memory store with 1-hour TTL.** Rendered audio is held in process memory and expires after one hour. Use a database or Cloud Storage for production.
- **Failed lines are skipped, not silent.** If a single line errors (e.g. invalid voice), the response includes an `errors` array and the stitched audio contains only successful lines in script order.

## Next steps

- Add a browser UI that lets users paste a script and play the stitched result inline. The `/narrate` and `/audio/<id>.mp3` endpoints are sufficient for this — no extra backend code is needed.
- Replace the in-memory store with Telnyx Cloud Storage and serve presigned URLs, mirroring [`ai-voiceover-studio-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-voiceover-studio-python).
- Add SSML emotion tags per line for character expression. See [Ultra SSML emotions](https://developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra#ssml-emotions).
