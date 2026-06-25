---
name: whatsapp-verify-otp
title: "WhatsApp Verify OTP"
description: "Send and verify one-time passwords via WhatsApp using the Telnyx Verify API."
language: python
framework: flask
telnyx_products: [Verify]
channel: [whatsapp]
---

# WhatsApp Verify OTP

Send and verify one-time passwords via WhatsApp using the Telnyx Verify API.

## Telnyx API Endpoints Used

- **Create Verification**: `POST /v2/verifications` - [API reference](https://developers.telnyx.com/api/verify/create-verification)
- **Submit Verification Code**: `POST /v2/verifications/by_phone_number/{phone_number}/actions/verify` - [API reference](https://developers.telnyx.com/api/verify/verify-verification-code)

## Architecture

```
  User requests OTP
        │
        ▼
  ┌──────────────────┐
  │ POST /verify/    │
  │ start            │
  └────────┬─────────┘
           │  Telnyx Verify API
           │  type: "whatsapp"
           ▼
  ┌──────────────────┐
  │ WhatsApp OTP     │ ── user receives code
  │ delivered        │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ POST /verify/    │ ── user submits code
  │ check            │
  └────────┬─────────┘
           │
           ▼
     ✓ Verified / ✗ Denied
```

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform - voice, messaging, SIP, AI, and IoT on one private, global network.

- **WhatsApp Business API** - send OTPs through WhatsApp for higher deliverability and read rates.
- **Verify API** - managed OTP generation, delivery, and validation across SMS, voice, and WhatsApp channels.
- **Global reach** - deliver verification codes to 200+ countries via WhatsApp.

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key | [Portal](https://portal.telnyx.com/api-keys) |
| `VERIFY_PROFILE_ID` | `string` | `your_value` | **yes** | Verify profile configured with WhatsApp channel | [Portal](https://portal.telnyx.com/verify/profiles) |
| `PORT` | `integer` | `5000` | no | HTTP server port | - |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/whatsapp-verify-otp-python
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

   - **Verify Profile** → Webhook URL → `https://<id>.ngrok.io/webhooks/verify`

## API Reference

### `POST /verify/start`

Send a WhatsApp OTP to a phone number.

```bash
curl -X POST http://localhost:5000/verify/start \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+12125551234"
  }'
```

**Response:**

```json
{
  "status": "sent",
  "phone": "+12125551234",
  "channel": "whatsapp"
}
```

### `POST /verify/check`

Submit the OTP code for verification.

```bash
curl -X POST http://localhost:5000/verify/check \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+12125551234",
    "code": "12345"
  }'
```

**Response:**

```json
{
  "status": "verified"
}
```

### `POST /webhooks/verify`

Receives delivery status webhooks from Telnyx (`verify.sent`, `verify.delivered`, `verify.completed`, `verify.failed`).

```bash
curl -X POST http://localhost:5000/webhooks/verify \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "event_type": "verify.delivered",
      "payload": {
        "phone_number": "+12125551234"
      }
    }
  }'
```

**Response:**

```json
{
  "status": "ok"
}
```

### `GET /health`

Returns service health status.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "verifications": 0
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or missing API key | Verify `TELNYX_API_KEY` in `.env` matches your key in the [Portal](https://portal.telnyx.com/api-keys) |
| `422 Unprocessable Entity` | Missing or malformed request fields | Check the request body against the API Reference above |
| OTP not received on WhatsApp | WABA not linked or phone not on WhatsApp | Ensure your WhatsApp Business Account (WABA) is linked to Telnyx and the recipient has WhatsApp installed |
| Webhook not received | Local server not publicly reachable | Expose it with a tunnel (e.g. ngrok) and set the webhook URL in your Verify Profile |
| `verify.failed` webhook | Code expired or delivery failed | Re-send the OTP with `/verify/start` |

## Related Examples

- [Verify Phone Number OTP Flow (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/verify-phone-number-otp-flow-python/README.md) - SMS OTP with voice fallback
- [Verify Multi-Channel Auth (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/verify-multi-channel-auth-python/README.md) - SMS, voice, and WhatsApp cascade

## Resources

- [Verify API Quickstart](https://developers.telnyx.com/docs/identity/verify/quickstart)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
