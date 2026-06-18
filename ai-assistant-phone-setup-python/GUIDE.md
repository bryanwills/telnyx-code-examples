# AI Assistant Phone Setup

> AI Assistant Phone Setup — create and configure a managed Telnyx AI Assistant and wire it to a phone number.

## What You'll Build

A production-ready **ai assistant phone setup** built with Python, Flask, and AI Inference.

| | |
|---|---|
| **Lines of code** | 95 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | AI Inference |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/ai-assistant-phone-setup-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (95 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/assistants` | Assistants |
| `GET` | `/assistants` | Assistants |
| `GET` | `/assistants/<assistant_id>` | <Assistant Id> |
| `PATCH` | `/assistants/<assistant_id>` | <Assistant Id> |
| `POST` | `/assistants/<assistant_id>/wire` | Wire |
| `POST` | `/assistants/<assistant_id>/test` | Test |
| `GET` | `/models` | Models |
| `GET` | `/health` | Health check |

### Key Functions

- **`create_assistant()`** — create assistant
- **`list_assistants()`** — list assistants
- **`get_assistant()`** — get assistant
- **`update_assistant()`** — update assistant
- **`wire_to_number()`** — wire to number
- **`test_assistant()`** — test assistant
- **`list_models()`** — list models
- **`health()`** — health

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/assistants \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t ai-assistant-phone-setup-python .
docker run --env-file .env -p 5000:5000 ai-assistant-phone-setup-python
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
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
