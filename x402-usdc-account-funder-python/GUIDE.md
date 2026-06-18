# x402 USDC Account Funder

> X402 USDC Account Funder — fund your Telnyx account with USDC cryptocurrency on the Base blockchain.

## What You'll Build

A production-ready **x402 usdc account funder** built with Python, Flask, and Migration, Number Porting.

| | |
|---|---|
| **Lines of code** | 76 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Migration, Number Porting |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Get Balance**: `GET /v2/balance` — [API reference](https://developers.telnyx.com/api/account/get-balance)
- **x402 Payment**: `POST /v2/x402/payments` — [x402 docs](https://developers.telnyx.com/docs/x402)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/x402-usdc-account-funder-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (76 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/quote` | Quote |
| `POST` | `/pay` | Pay |
| `GET` | `/balance` | Balance |
| `GET` | `/info` | Info |
| `GET` | `/quotes` | Quotes |
| `GET` | `/payments` | Payments |
| `GET` | `/health` | Health check |

### Key Functions

- **`get_quote()`** — get quote
- **`submit_payment()`** — submit payment
- **`get_balance()`** — get balance
- **`payment_info()`** — payment info
- **`list_quotes()`** — list quotes
- **`list_payments()`** — list payments
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
curl -X POST http://localhost:5000/quote \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t x402-usdc-account-funder-python .
docker run --env-file .env -p 5000:5000 x402-usdc-account-funder-python
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
