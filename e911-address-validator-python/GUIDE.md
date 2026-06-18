# E911 Address Validator — validate and provision E911 addresses via API.

> Application. Built with Telnyx E911, Migration, Number Porting.

## What You'll Build

A production-ready **e911 address validator — validate and provision e911 addresses via api** built with Python, Flask, and E911, Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 50 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | E911, Migration, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **List Phone Numbers**: `GET /v2/phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-phone-numbers)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/e911-address-validator-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (50 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/e911/validate` | Validate |
| `POST` | `/e911/assign` | Assign |
| `GET` | `/e911/addresses` | Addresses |
| `GET` | `/health` | Health check |

### Key Functions

- **`validate_address()`** — validate address
- **`assign_e911()`** — assign e911
- **`list_addresses()`** — list addresses
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
curl -X POST http://localhost:5000/e911/validate \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t e911-address-validator-python .
docker run --env-file .env -p 5000:5000 e911-address-validator-python
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
