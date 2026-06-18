# Migrate from ElevenLabs

> Migrate from ElevenLabs — import ElevenLabs voice configurations to Telnyx TTS with voice mapping and cost comparison.

## What You'll Build

A production-ready **migrate from elevenlabs** built with Python, Flask, and AI Assistants, Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 98 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | AI Assistants, Migration, Number Porting |
| **Channels** | voice |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **TTS Generate**: `POST /v2/ai/generate` — [API reference](https://developers.telnyx.com/api/inference/generate)
- **Chat Completions**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **List Models**: `GET /v2/ai/models` — [API reference](https://developers.telnyx.com/api/inference/list-models)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/migrate-from-elevenlabs-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (98 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/audit/elevenlabs` | Elevenlabs |
| `POST` | `/migrate/voice-config` | Voice Config |
| `GET` | `/mapping/voices` | Voices |
| `GET` | `/cost-comparison` | Cost Comparison |
| `POST` | `/test-tts` | Test Tts |
| `GET` | `/migration-log` | Migration Log |
| `GET` | `/health` | Health check |

### Key Functions

- **`audit_elevenlabs()`** — audit elevenlabs
- **`migrate_voice()`** — migrate voice
- **`voice_mapping()`** — voice mapping
- **`cost_comparison()`** — cost comparison
- **`test_tts()`** — test tts
- **`get_log()`** — get log
- **`health()`** — health

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

Expose your local server for Telnyx webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and configure it in the [Telnyx Portal](https://portal.telnyx.com):

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X GET http://localhost:5000/audit/elevenlabs \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t migrate-from-elevenlabs-python .
docker run --env-file .env -p 5000:5000 migrate-from-elevenlabs-python
```

### Makefile

```bash
make setup    # Install dependencies
make run      # Start the server
make docker   # Build and run in Docker
```

## Customize & Extend

- Replace in-memory storage with PostgreSQL or Redis for production
- Add authentication to your API endpoints
- Set up monitoring and alerting
- Add conversation memory for multi-turn AI interactions
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
