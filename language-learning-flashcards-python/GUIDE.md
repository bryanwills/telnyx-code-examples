# Build Voice Flashcards with Telnyx

Listen to a phrase, repeat it back, and get instant pronunciation feedback. TTS speaks the flashcard, you record your voice, STT transcribes it, and Inference scores your pronunciation.

## How It Works

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

## Telnyx Products Used

- **Text-to-Speech** — `POST /v2/text-to-speech/speech` (Ultra voice with `language_boost`)
- **Speech-to-Text** — `POST /v2/ai/audio/transcriptions` (Whisper, multipart upload)
- **AI Inference** — `POST /v2/ai/chat/completions` (Kimi-K2.6, scores pronunciation)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- A Telnyx API v2 key from the [Portal](https://portal.telnyx.com/api-keys)
- A browser with microphone access

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
# * Running on http://127.0.0.1:5050
```

## Step 4 — Use the flashcards

1. Open `http://127.0.0.1:5050/` in your browser.
2. Pick a deck (Spanish Greetings, Spanish Numbers, etc.).
3. Listen to the phrase — audio autoplays.
4. Click **Record**, repeat the phrase, click **Stop**.
5. See your score: correct (green), close (yellow), or wrong (red).
6. Compare your spoken text against the target.
7. Click **Next card** or **Try again**.

## How the scoring works

The backend calls Telnyx Inference with a system prompt that tells the model to compare the target phrase against what the user said, and return JSON with a score and feedback:

```python
system_prompt = (
    "You are a language pronunciation checker. "
    "Compare the target phrase with what the user said. "
    'Return ONLY valid JSON: {"score": "correct"|"close"|"wrong", "feedback": "one short sentence tip"}'
)
```

The model evaluates whether the spoken text matches the target phrase, accounting for minor accent differences (correct), noticeable errors (close), or completely wrong/unintelligible speech (wrong).

## Flashcard decks

The app ships with 4 pre-built decks:

| Deck | Language | Cards |
|------|----------|-------|
| Spanish — Greetings | Spanish | 8 |
| Spanish — Numbers | Spanish | 6 |
| Spanish — Common phrases | Spanish | 8 |
| French — Greetings | French | 6 |

Add more decks by editing `FLASHCARD_DECKS` in `app.py`. Each card has a `phrase` (what TTS speaks and what you repeat) and a `translation` (shown as a hint).

## Notes and caveats

- **One env var required.** `TELNYX_API_KEY`. The rest have defaults.
- **In-memory storage.** Audio expires after `TEMP_FILE_TTL_MINUTES` (default 30 min).
- **API key never reaches the browser.** All Telnyx calls are server-side.
- **Kimi-K2.6 is a reasoning model.** Scoring takes ~5-10 seconds. The UI shows "Checking your pronunciation..." during this time.
- **Score reliability.** The model is lenient with accents but strict with completely wrong words. If you get "wrong" but think you said it correctly, check if STT transcribed it right — the score depends on STT accuracy.
- **Port 5050.** Defaults to 5050 to avoid macOS AirPlay on 5000.

## Next steps

- Add more languages and decks by updating `FLASHCARD_DECKS`.
- Add a streak counter or score tracking across a deck.
- Add difficulty levels (speed, no-translation hint).
- Replace in-memory store with persistent storage for progress tracking.
