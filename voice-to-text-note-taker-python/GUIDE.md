# Build a Telnyx Speech Translator

Record your voice, transcribe it, translate it, and hear it in another language. STT → AI Inference → TTS on one platform.

## How It Works

```
Browser microphone or audio upload
              ↓
       POST /transcribe
              ↓
 Telnyx Speech-to-Text REST API
              ↓
      Editable transcript
              ↓
        POST /translate
              ↓
     Telnyx Inference API
              ↓
      Editable translation
              ↓
        POST /synthesize
              ↓
 Telnyx Text-to-Speech API
              ↓
   Audio playback and download
```

## Telnyx Products Used

- **Speech-to-Text** — `POST /v2/ai/audio/transcriptions` (Whisper, multipart upload)
- **AI Inference** — `POST /v2/ai/chat/completions` (Kimi-K2.6, OpenAI-compatible)
- **Text-to-Speech** — `POST /v2/text-to-speech/speech` (Ultra voice with `language_boost`)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- A Telnyx API v2 key from the [Portal](https://portal.telnyx.com/api-keys)
- A browser with microphone access

No phone number, TeXML application, or webhook endpoint is required.

## Step 1 — Configure environment

```bash
cp .env.example .env
# Edit .env:
#   TELNYX_API_KEY=your_key
#   STT_MODEL=openai/whisper-large-v3-turbo
#   TRANSLATION_MODEL=moonshotai/Kimi-K2.6
#   TTS_VOICE=Telnyx.Ultra.01eaafa9-308a-4276-a017-6ab0cf061b1f
```

## Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

## Step 3 — Run the app

```bash
python app.py
# * Running on http://127.0.0.1:5050
```

## Step 4 — Record or upload audio

1. Open `http://127.0.0.1:5050/` in your browser.
2. Click **Record** to use your microphone, or **Upload audio file** to use an existing file.
3. The audio preview appears.
4. Click **Transcribe with Telnyx** to send it to STT.

## Step 5 — Review and translate

1. The transcript appears in the left panel (editable).
2. Pick a target language from the dropdown (Spanish is default).
3. Click **Translate to Spanish** (or your selected language).
4. The translation appears in the right panel (editable).

## Step 6 — Generate translated speech

1. Click **Generate Spanish audio** (or your selected language).
2. The audio player appears with the translated speech.
3. Click download to save the audio as an MP3.

## Step 7 — Download everything

- **Original transcript** — click "Download original .txt"
- **Translation** — click "Download translation .txt"
- **Audio** — click "Download {language} audio"

Filenames include the language and date:
```
original-transcript-2026-08-05.txt
spanish-translation-2026-08-05.txt
spanish-audio-2026-08-05.mp3
```

## How translation works

The backend calls Telnyx Inference (`POST /v2/ai/chat/completions`) with:

```python
system_prompt = (
    f"You are a professional translator.\n\n"
    f"Translate the supplied text from its original language into {target_language}.\n\n"
    f"Requirements:\n"
    f"- Preserve the original meaning.\n"
    f"- Preserve names, numbers, technical terms, and formatting.\n"
    f"- Do not summarize.\n"
    f"- Do not explain the translation.\n"
    f"- Return only the translated text."
)
# temperature=0.1, max_tokens=2000
```

The model is `moonshotai/Kimi-K2.6` (native Telnyx, no external API key). Low temperature ensures consistent translations. `max_tokens=2000` accounts for the model's reasoning tokens.

## How TTS voice selection works

The app uses a single Ultra voice (Clara by default) with `voice_settings.language_boost` set to the target language. Ultra supports 36+ languages, so one voice covers all 8 target languages.

To use a different voice:

```bash
curl -H "Authorization: Bearer $TELNYX_API_KEY" \
  https://api.telnyx.com/v2/text-to-speech/voices \
  | jq '.voices[] | select(.id | startswith("Telnyx.Ultra."))'
```

Set the UUID in `TTS_VOICE` in your `.env`.

## Notes and caveats

- **One env var required.** `TELNYX_API_KEY`. The rest have sensible defaults.
- **In-memory storage.** Everything expires after `TEMP_FILE_TTL_MINUTES` (default 30 min).
- **API key never reaches the browser.** All Telnyx calls are server-side.
- **Audio file limits.** Max 25 MB upload, validated by extension and size.
- **Translation limits.** Max 10,000 characters. TTS max 3,000 characters per call.
- **Port 5050.** Defaults to 5050 to avoid macOS AirPlay on 5000.

## Next steps

- Add more target languages by updating `TARGET_LANGUAGES` and `LANGUAGE_BOOST_MAP` in `app.py`.
- Add a language detection display from the STT response.
- Add chunked TTS for translations longer than 3,000 characters.
- Replace in-memory store with Telnyx Cloud Storage for persistent, shareable URLs.
