# IVR Prompt Generator

> Generate professional IVR/phone system prompts. AI writes caller-friendly scripts from business descriptions, TTS renders in multiple voices, test via live Telnyx call playback.

## What You'll Build

A production-ready **ivr prompt generator** built with Python, Flask, and Voice, AI Inference, Cloud Storage.

| | |
|---|---|
| **Lines of code** | 268 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Voice, AI Inference, Cloud Storage |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **AI Inference (script writing)**: `POST /v2/ai/chat/completions` -- [ref](https://developers.telnyx.com/api/inference/chat-completions)
- **TTS Generate**: `POST /v2/ai/generate` -- [ref](https://developers.telnyx.com/api/inference/generate)
- **Create Call (preview)**: `POST /v2/calls` -- [ref](https://developers.telnyx.com/api/call-control/create-call)
- **Speak (playback)**: `POST /v2/calls/{id}/actions/speak` -- [ref](https://developers.telnyx.com/api/call-control/speak)
- **Cloud Storage**: `PUT https://storage.telnyx.com/{bucket}/{key}` -- [docs](https://developers.telnyx.com/docs/cloud-storage)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ivr-prompt-generator-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (268 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/prompts/generate` | Generate |
| `POST` | `/prompts/<set_id>/preview` | Preview |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/prompts/<set_id>` | <Set Id> |
| `GET` | `/prompt-types` | Prompt Types |
| `GET` | `/health` | Health check |

### Key Functions

- **`inference()`** — inference
- **`tts_generate()`** — tts generate
- **`telnyx_post()`** — telnyx post
- **`upload_to_storage()`** — upload to storage
- **`generate_prompts()`** — generate prompts
- **`preview_prompt()`** — preview prompt
- **`handle_voice()`** — handle voice
- **`get_prompt_set()`** — get prompt set
- **`get_prompt_types()`** — get prompt types
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
curl -X POST http://localhost:5000/prompts/generate \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t ivr-prompt-generator-python .
docker run --env-file .env -p 5000:5000 ivr-prompt-generator-python
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
