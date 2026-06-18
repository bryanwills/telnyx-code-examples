# Verify Multi-Channel Auth

> Verify Multi-Channel Auth — multi-channel verification: SMS first, fallback to voice call, then WhatsApp. Cascading 2FA.

## What You'll Build

A production-ready **verify multi-channel auth** built with Python, Flask, and Migration, Number Porting, Verify, WhatsApp.

| | |
|---|---|
| **Lines of code** | 97 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Number Porting, Verify, WhatsApp |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Create Verification**: `POST /v2/verifications` — [API reference](https://developers.telnyx.com/api/verify/create-verification)
- **Submit Verification Code**: `POST /v2/verifications/{id}/actions/verify` — [API reference](https://developers.telnyx.com/api/verify/verify-code)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/verify-multi-channel-auth-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (97 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/verify/start` | Start |
| `POST` | `/verify/check` | Check |
| `POST` | `/verify/escalate/<vid>` | <Vid> |
| `POST` | `/verify/cascade` | Cascade |
| `GET` | `/verifications` | Verifications |
| `GET` | `/health` | Health check |

### Key Functions

- **`start_verification()`** — start verification
- **`check_verification()`** — check verification
- **`escalate_channel()`** — escalate channel
- **`cascade_verify()`** — cascade verify
- **`list_verifications()`** — list verifications
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
curl -X POST http://localhost:5000/verify/start \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t verify-multi-channel-auth-python .
docker run --env-file .env -p 5000:5000 verify-multi-channel-auth-python
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
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
