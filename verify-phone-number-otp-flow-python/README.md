---
name: verify-phone-number-otp-flow
title: "Verify Phone Number OTP Flow"
description: "Verify Phone Number OTP Flow — Telnyx Verify API with SMS primary and voice call fallback."
language: python
framework: flask
telnyx_products: [Verify]
channel: [voice]
---

# Verify Phone Number OTP Flow

Verify Phone Number OTP Flow — Telnyx Verify API with SMS primary and voice call fallback.

## Telnyx API Endpoints Used

- **Create Verification**: `POST /v2/verifications` — [API reference](https://developers.telnyx.com/api/verify/create-verification)

## Architecture

```
  User requests verification
        │
        ▼
  ┌──────────────────┐
  │ Generate OTP     │
  └────────┬─────────┘
           │
           ├──► SMS code
           │
           ▼
  ┌──────────────────┐
  │ Verify code      │ ── user submits OTP
  └────────┬─────────┘
           │
           ▼
     ✓ Verified / ✗ Denied
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `VERIFY_PROFILE_ID` | `string` | `your_value` | **yes** | Verify profile id | — |
| `PORT` | `integer` | `5000` | no | HTTP server port | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/verify-phone-number-otp-flow-python
cp .env.example .env    # ← fill in your credentials
pip install -r requirements.txt
python app.py           # starts on http://localhost:5000
```

### Webhook Configuration

1. Expose your local server:

   ```bash
   ngrok http 5000
   ```

2. Copy the HTTPS URL and configure in [Telnyx Portal](https://portal.telnyx.com):

   - **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

### Docker

```bash
docker build -t verify-phone-number-otp-flow-python .
docker run --env-file .env -p 5000:5000 verify-phone-number-otp-flow-python
```

## API Reference

### `POST /verify/start`

Triggers start

```bash
curl -X POST http://localhost:5000/verify/start \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125551234",
    "channel": "sms"
  }'
```

**Response:**

```json
{
  "verification_id": "ver-abc123",
  "status": "pending",
  "channel": "sms",
  "phone": "+12125551234"
}
```

### `POST /verify/voice-fallback`

Triggers voice-fallback

```bash
curl -X POST http://localhost:5000/verify/voice-fallback \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125551234",
    "channel": "sms"
  }'
```

**Response:**

```json
{
  "verification_id": "ver-abc123",
  "status": "pending",
  "channel": "sms",
  "phone": "+12125551234"
}
```

### `POST /verify/check`

Triggers check

```bash
curl -X POST http://localhost:5000/verify/check \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125551234",
    "channel": "sms"
  }'
```

**Response:**

```json
{
  "verification_id": "ver-abc123",
  "status": "pending",
  "channel": "sms",
  "phone": "+12125551234"
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

- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
