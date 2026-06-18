# Click-to-Call WebRTC with AI Assist

> Click-to-Call WebRTC with AI Assist — browser-based calling with real-time AI coaching sidebar.

## What You'll Build

A production-ready **click-to-call webrtc with ai assist** built with Python, Flask, and AI Inference.

| | |
|---|---|
| **Lines of code** | 72 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | AI Inference |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Telephony Credentials**: `POST /v2/telephony_credentials` — [API reference](https://developers.telnyx.com/api/webrtc/create-telephony-credential)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/click-to-call-webrtc-with-ai-assist-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (72 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webrtc/token` | Token |
| `POST` | `/coaching` | Coaching |
| `GET` | `/health` | Health check |
| `GET` | `/` | Root |

### Key Functions

- **`index()`** — index
- **`get_token()`** — get token
- **`get_coaching()`** — get coaching
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
curl -X POST http://localhost:5000/webrtc/token \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t click-to-call-webrtc-with-ai-assist-python .
docker run --env-file .env -p 5000:5000 click-to-call-webrtc-with-ai-assist-python
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
