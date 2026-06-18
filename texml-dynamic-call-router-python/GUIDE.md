# TeXML Dynamic Call Router

> TeXML Dynamic Call Router — time-of-day and caller-based routing with TeXML responses.

## What You'll Build

A production-ready **texml dynamic call router** built with Python, Flask, and Migration, Number Porting, Voice.

| | |
|---|---|
| **Lines of code** | 57 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Number Porting, Voice |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **TeXML Webhooks**: Telnyx sends HTTP requests to your TeXML endpoints — [TeXML docs](https://developers.telnyx.com/docs/voice/texml)
- **TeXML Dial**: Route calls to SIP, PSTN, or conference — [reference](https://developers.telnyx.com/docs/voice/texml/verbs/dial)
- **TeXML Gather**: Collect DTMF or speech input — [reference](https://developers.telnyx.com/docs/voice/texml/verbs/gather)
- **TeXML Say**: Text-to-speech — [reference](https://developers.telnyx.com/docs/voice/texml/verbs/say)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/texml-dynamic-call-router-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (57 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/texml/route` | Route |
| `POST` | `/texml/recording` | Recording |
| `POST` | `/vip` | Vip |
| `GET` | `/calls` | Calls |
| `GET` | `/health` | Health check |

### Key Functions

- **`route_call()`** — route call
- **`handle_recording()`** — handle recording
- **`add_vip()`** — add vip
- **`list_calls()`** — list calls
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
curl -X POST http://localhost:5000/texml/route \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t texml-dynamic-call-router-python .
docker run --env-file .env -p 5000:5000 texml-dynamic-call-router-python
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
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
