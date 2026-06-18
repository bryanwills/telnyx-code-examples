# Build a x402 USDC Account Funder

X402 USDC Account Funder — fund your Telnyx account with USDC cryptocurrency on the Base blockchain.

## How It Works

```
  API Request (fund account)
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx Balance API (check current)
           │
           ├──► Base Blockchain
           │    └──► USDC transfer (ERC-20)
           │
           ├──► Telnyx Billing API (verify credit)
           │
           └──► Funding confirmation
```

## Telnyx Products Used

- **Migration**
- **Number Porting** — phone number search, purchase, and configuration

## API Endpoints

- **Get Balance**: `GET /v2/balance` — [API reference](https://developers.telnyx.com/api/account/get-balance)
- **x402 Payment**: `POST /v2/x402/payments` — [x402 docs](https://developers.telnyx.com/docs/x402)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/x402-usdc-account-funder-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (76 lines). Here's what each piece does.

### Business Logic

- **`get_quote()`** — Makes an API call and processes the response.
- **`submit_payment()`** — Makes an API call and processes the response.
- **`get_balance()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/quote` | Get Quote |
| `POST` | `/pay` | Submit Payment |
| `GET` | `/balance` | Get Balance |
| `GET` | `/info` | Payment Info |
| `GET` | `/quotes` | List Quotes |
| `GET` | `/payments` | List Payments |
| `GET` | `/health` | Health check |

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Trigger the workflow:**

```bash
curl -X POST http://localhost:5000/quote \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/balance | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Deploy

```bash
# Docker
docker build -t x402-usdc-account-funder-python .
docker run --env-file .env -p 5000:5000 x402-usdc-account-funder-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
