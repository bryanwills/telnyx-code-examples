# Update AI Assistant

> Update an existing Telnyx AI Assistant's configuration, model, system prompt, and tools via the API.

## What You'll Build

A production-ready **update ai assistant** built with Python, Flask, and AI Assistants.

| | |
|---|---|
| **Lines of code** | 91 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | AI Assistants |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Update AI Assistant**: `PATCH /v2/ai/assistants/{id}` -- [API reference](https://developers.telnyx.com/api/ai/update-assistant)
- **Get AI Assistant**: `GET /v2/ai/assistants/{id}` -- [API reference](https://developers.telnyx.com/api/ai/get-assistant)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/update-ai-assistant-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (91 lines). Here's how it's structured:

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

## Production Deployment

### Docker

```bash
docker build -t update-ai-assistant-python .
docker run --env-file .env -p 5000:5000 update-ai-assistant-python
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
