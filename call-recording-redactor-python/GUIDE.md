# Build an AI Call Recording Redactor

AI Call Recording Redactor — transcribe call audio and redact PII (names, credit cards, SSNs, addresses, phone numbers, emails) via Telnyx STT + AI Inference. Supports both direct transcript redaction and audio file upload.

## How It Works

```
  Audio file or transcript
        │
        ▼
  ┌──────────────────────────┐
  │ Your App                 │
  └────────┬─────────────────┘
           │
           ├──► Telnyx STT (audio → text)
           │
           ├──► Telnyx AI Inference (PII detection + redaction)
           │
           ▼
     Redacted transcript + redaction map (JSON)
```

## Telnyx Products Used

- **AI Inference (Audio Transcriptions)** — Speech-to-text via `distil-whisper/distil-large-v2`
- **AI Inference (Chat Completions)** — LLM identifies and replaces PII in the transcript

## API Endpoints

- **Audio Transcriptions**: `POST /v2/ai/audio/transcriptions` — [API reference](https://developers.telnyx.com/api/inference/create-transcription)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/call-recording-redactor-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py`. Here's what each piece does.

### Two Modes

1. **Direct transcript (`POST /redact`)** — submit text, get redacted text. No audio needed. Fast and easy to demo.
2. **Audio file (`POST /redact/audio`)** — upload a WAV/MP3, transcribe via STT, then redact. Full pipeline.

### Helper Functions

- **`call_inference()`** — Sends the redaction prompt to Telnyx AI Inference. Uses `max_tokens=6000` and `timeout=120s` for reasoning models. Strips markdown fences.
- **`transcribe_audio()`** — Uploads an audio file to the Telnyx STT API (`distil-whisper/distil-large-v2`) and returns the transcript text.
- **`redact_transcript()`** — Sends the transcript to the LLM with the PII redaction system prompt and returns structured JSON.

### PII Types Redacted

| Type | Placeholder |
|------|-------------|
| Name | `[NAME]` |
| Credit card | `[CREDIT_CARD]` |
| SSN | `[SSN]` |
| Phone | `[PHONE]` |
| Email | `[EMAIL]` |
| Address | `[ADDRESS]` |
| Date of birth | `[DOB]` |
| Account number | `[ACCOUNT_NUMBER]` |

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/redact` | Redact PII from a text transcript |
| `POST` | `/redact/audio` | Upload audio → STT → redact |
| `GET` | `/redactions` | List redaction jobs |
| `GET` | `/redactions/<id>` | Get a specific redaction |
| `GET` | `/health` | Health check |

The audio endpoint transcribes then redacts:

```python
@app.route("/redact/audio", methods=["POST"])
def redact_audio():
    file = request.files["file"]
    file_bytes = file.read()
    transcript = transcribe_audio(file_bytes, file.filename, language)
    result = redact_transcript(transcript)
    result["source"] = f"audio:{file.filename}"
    result["original_transcript"] = transcript
    return jsonify(result), 201
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Redact a text transcript:**

```bash
curl -X POST http://localhost:5000/redact \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Hi, this is John Smith calling. My card number is 4532-1234-5678-9012 and my SSN is 123-45-6789. You can reach me at 555-867-5309 or john.smith@email.com. I live at 123 Main St, Springfield IL 62701."}' | python3 -m json.tool
```

**Redact from an audio file:**

```bash
curl -X POST http://localhost:5000/redact/audio \
  -F "file=@recording.wav" | python3 -m json.tool
```

**List redactions:**

```bash
curl http://localhost:5000/redactions | python3 -m json.tool
```

**Get a specific redaction:**

```bash
curl http://localhost:5000/redactions/red-<id> | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — persist redactions in PostgreSQL or Redis
- **Call recording webhooks** — wire `POST /redact/audio` to Telnyx `call.recording.saved` webhooks for automatic processing
- **Audio masking** — beyond transcript redaction, bleep/mute the original audio at PII timestamps
- **Batch processing** — queue multiple recordings for async redaction
- **Custom PII types** — add domain-specific PII (patient IDs, policy numbers, etc.)
- **Compliance** — support GDPR/HIPAA/PCI-DSS redaction requirements
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/call-recording-redactor-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
