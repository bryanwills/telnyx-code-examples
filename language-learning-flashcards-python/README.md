---
name: language-learning-flashcards
title: "Voice Flashcards"
description: "Listen to a phrase, repeat it back, and get instant pronunciation feedback. TTS speaks, you repeat, STT transcribes, Inference scores — interactive language learning powered by all three Telnyx AI primitives."
language: python
framework: flask
telnyx_products: [Text-to-Speech, Speech-to-Text, AI Inference]
channel: [api]
---

# Voice Flashcards

Listen to a phrase in Spanish (or French), repeat it back, and get instant pronunciation feedback. Telnyx TTS speaks the flashcard, you record your voice, Telnyx STT transcribes it, and Telnyx Inference scores your pronunciation as correct, close, or wrong.

Interactive language learning powered by all three Telnyx AI primitives — TTS, STT, and Inference — on one platform. No phone, no database, no Cloud Storage.

## Architecture

```
  Telnyx TTS plays flashcard phrase
              ↓
      You listen and repeat
              ↓
  Browser records your voice
              ↓
     POST /check (audio + target phrase)
              ↓
  Telnyx STT transcribes your speech
              ↓
  Telnyx Inference compares + scores
              ↓
   Score: correct / close / wrong
   + feedback + target vs spoken
              ↓
       Next card or try again
```

## Telnyx API Endpoints Used

- **Text-to-Speech**: `POST /v2/text-to-speech/speech` — speaks the flashcard phrase in the target language
  - Voice: Ultra Clara (`Telnyx.Ultra.01eaafa9-...`) with `language_boost` per language
- **Speech-to-Text**: `POST /v2/ai/audio/transcriptions` — transcribes your spoken answer
  - Model: `openai/whisper-large-v3-turbo`
- **AI Inference**: `POST /v2/ai/chat/completions` — compares your spoken text against the target phrase and returns a score + feedback
  - Model: `moonshotai/Kimi-K2.6`

> **The browser never receives the Telnyx API key.** All API calls are server-side.

## How It Works

1. **Pick a deck** — choose from Spanish Greetings, Spanish Numbers, Spanish Common Phrases, or French Greetings.
2. **Listen** — TTS plays the flashcard phrase in the target language. Audio autoplays.
3. **Repeat** — click Record, speak the phrase, click Stop.
4. **Score** — STT transcribes your speech, Inference compares it against the target, and returns a score (correct / close / wrong) with feedback.
5. **Next** — move to the next card or retry the current one.

## Why Telnyx

Telnyx AI Communications Infrastructure exposes TTS, STT, and Inference as REST endpoints on one private backbone. This example uses all three in one interactive loop. TTS speaks the phrase, STT listens to your answer, and Inference evaluates it — all on one platform, one API key, no external services. The browser captures audio; the server does the rest.

## Environment Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `TELNYX_API_KEY` | `string` | **yes** | Telnyx API v2 key |
| `STT_MODEL` | `string` | no | STT model (default: `openai/whisper-large-v3-turbo`) |
| `TRANSLATION_MODEL` | `string` | no | Inference model for scoring (default: `moonshotai/Kimi-K2.6`) |
| `TTS_VOICE` | `string` | no | TTS voice UUID (default: Clara) |
| `TTS_AUDIO_FORMAT` | `string` | no | Audio format (default: mp3) |
| `MAX_AUDIO_SIZE_MB` | `int` | no | Max upload size (default: 25) |
| `TEMP_FILE_TTL_MINUTES` | `int` | no | In-memory TTL (default: 30) |
| `PORT` | `int` | no | Flask port (default: 5050) |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/language-learning-flashcards-python
cp .env.example .env    # ← fill in your TELNYX_API_KEY
pip install -r requirements.txt
python app.py           # starts on http://127.0.0.1:5050
```

## API Reference

See [`API.md`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/language-learning-flashcards-python/API.md) for the full endpoint reference.

## Flashcard Decks

| Deck | Language | Cards |
|------|----------|-------|
| Spanish — Greetings | Spanish | 8 |
| Spanish — Numbers | Spanish | 6 |
| Spanish — Common phrases | Spanish | 8 |
| French — Greetings | French | 6 |

Add more decks by editing `FLASHCARD_DECKS` in `app.py`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Missing `TELNYX_API_KEY` | Set it in `.env` |
| TTS audio doesn't play | Browser blocked autoplay | Click the audio player manually |
| Score always "wrong" | STT didn't transcribe correctly | Speak clearly, minimize background noise |
| Inference returns "invalid response" | Model returned non-JSON | Retry — Kimi sometimes wraps output in markdown |
| Browser mic not working | Permission denied | Check browser microphone permissions |
| Port 5000 in use | macOS AirPlay | App defaults to `PORT=5050` |

## Related Examples

- [`ai-language-learning-phone-tutor-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-language-learning-phone-tutor-python) — phone-based language tutor
- [`ai-content-translator-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-content-translator-python) — STT + translate + TTS pipeline
- [`multi-character-narrator-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/multi-character-narrator-python) — multi-voice TTS with emotions
- [`ai-voiceover-studio-python`](https://github.com/team-telnyx/telnyx-code-examples/tree/main/ai-voiceover-studio-python) — voice-over with AI direction

## Agent Discovery

This example is part of the [Telnyx Code Examples](https://github.com/team-telnyx/telnyx-code-examples) catalog.

- **Agent signup**: [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md)
- **Agent CLI**: [github.com/team-telnyx/ai/tree/main/cli](https://github.com/team-telnyx/ai/tree/main/cli)
- **Agent skills**: [github.com/team-telnyx/ai/tree/main/skills](https://github.com/team-telnyx/ai/tree/main/skills)
- **Telnyx AI repo**: [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLM-optimized docs**: [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt)
- **Example index**: [`llms.txt`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/llms.txt)
- **Telnyx CLI (human)**: [developers.telnyx.com/development/cli](https://developers.telnyx.com/development/cli)

## Resources

- TTS: [developers.telnyx.com/docs/voice/tts](https://developers.telnyx.com/docs/voice/tts)
- STT: [developers.telnyx.com/api/inference/transcribe](https://developers.telnyx.com/api/inference/transcribe)
- Inference: [developers.telnyx.com/api/inference/chat-completions](https://developers.telnyx.com/api/inference/chat-completions)
- Ultra TTS: [developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra](https://developers.telnyx.com/docs/voice/tts/providers/telnyx/ultra)
- Repo CONTRIBUTING.md: [github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md](https://github.com/team-telnyx/telnyx-code-examples/blob/main/CONTRIBUTING.md)
