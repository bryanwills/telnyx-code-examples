---
name: x402-usdc-account-funder
title: "x402 USDC Account Funder"
description: "X402 USDC Account Funder — fund your Telnyx account with USDC cryptocurrency on the Base blockchain."
language: python
framework: flask
telnyx_products: []
---

# x402 USDC Account Funder

X402 USDC Account Funder — fund your Telnyx account with USDC cryptocurrency on the Base blockchain.

## Telnyx API Endpoints Used

- **Get Balance**: `GET /v2/balance` — [API reference](https://developers.telnyx.com/api/account/get-balance)
- **x402 Payment**: `POST /v2/x402/payments` — [x402 docs](https://developers.telnyx.com/docs/x402)

## Architecture

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

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/x402-usdc-account-funder-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

### Docker

```bash
docker build -t x402-usdc-account-funder-python .
docker run --env-file .env -p 5000:5000 x402-usdc-account-funder-python
```

## API Reference

### `POST /quote`

Triggers quote

```bash
curl -X POST http://localhost:5000/quote \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `POST /pay`

Triggers pay

```bash
curl -X POST http://localhost:5000/pay \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "id": "item-1750280400",
  "status": "created",
  "created_at": "2026-07-15T14:30:00Z"
}
```

### `GET /balance`

Returns balance

```bash
curl http://localhost:5000/balance
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /info`

Returns info

```bash
curl http://localhost:5000/info
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /quotes`

Returns quotes

```bash
curl http://localhost:5000/quotes
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /payments`

Returns payments

```bash
curl http://localhost:5000/payments
```

**Response:**

```json
{
  "items": [
    {
      "id": "item-001",
      "status": "active",
      "created_at": "2026-07-15T14:30:00Z"
    }
  ]
}
```

### `GET /health`

Returns health

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "uptime_seconds": 3842,
  "active_sessions": 2,
  "version": "1.0.0"
}
```

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
