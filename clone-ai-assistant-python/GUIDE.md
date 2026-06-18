# Production-ready Flask application for cloning AI Assistants via Telnyx.

> Application. Built with Telnyx AI Assistants, Migration, Number Porting.

## What You'll Build

A production-ready **production-ready flask application for cloning ai assistants via telnyx** built with Python, Flask, and AI Assistants, Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 131 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | AI Assistants, Migration, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Retrieve AI Assistant**: `GET /v2/ai/assistants/{id}` — [API reference](https://developers.telnyx.com/api/ai-assistants/get-assistant)
- **Create AI Assistant**: `POST /v2/ai/assistants` — [API reference](https://developers.telnyx.com/api/ai-assistants/create-assistant)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/clone-ai-assistant-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (131 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/assistants/<assistant_id>` | <Assistant Id> |
| `POST` | `/assistants/<assistant_id>/clone` | Clone |

### Key Functions

- **`get_assistant_details()`** — get assistant details
- **`clone_assistant()`** — clone assistant
- **`get_assistant()`** — get assistant
- **`clone_assistant_endpoint()`** — clone assistant endpoint

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
curl -X GET http://localhost:5000/assistants/<assistant_id> \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t clone-ai-assistant-python .
docker run --env-file .env -p 5000:5000 clone-ai-assistant-python
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
