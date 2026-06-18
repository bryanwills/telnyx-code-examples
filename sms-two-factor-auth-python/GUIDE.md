# Production-ready OTP 2FA system with Flask and Telnyx SMS.

> SMS application. Built with Telnyx Cloud Storage, Migration, Number Porting, SMS/MMS.

## What You'll Build

A production-ready **production-ready otp 2fa system with flask and telnyx sms** built with Python, Flask, and Cloud Storage, Migration, Number Porting, SMS/MMS, Verify.

| | |
|---|---|
| **Lines of code** | 201 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Cloud Storage, Migration, Number Porting, SMS/MMS, Verify |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Send Message (OTP)**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/sms-two-factor-auth-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (201 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/request-otp` | Request Otp |
| `POST` | `/auth/verify-otp` | Verify Otp |
| `GET` | `/auth/otp-status` | Otp Status |

### Key Functions

- **`generate_otp()`** — generate otp
- **`send_otp_sms()`** — send otp sms
- **`store_otp()`** — store otp
- **`verify_otp()`** — verify otp
- **`get_otp_status()`** — get otp status
- **`request_otp()`** — request otp
- **`verify_otp_endpoint()`** — verify otp endpoint
- **`otp_status()`** — otp status

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

- **Messaging Profile** → Inbound Webhook → `https://<id>.ngrok.io/webhooks/sms`

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or send an SMS to your Telnyx number to trigger the messaging workflow.

## Production Deployment

### Docker

```bash
docker build -t sms-two-factor-auth-python .
docker run --env-file .env -p 5000:5000 sms-two-factor-auth-python
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
- [Messaging Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
