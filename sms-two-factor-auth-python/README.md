# Sms Two Factor Auth

Production-ready OTP 2FA system with Flask and Telnyx SMS.

## Telnyx Products Used

- Verify API

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
                                          │
                                          ▼
                                  Customer Notification
                                      (SMS/Voice)
```

## Quick Start

### Prerequisites

- Python 3.8+
- A [Telnyx account](https://portal.telnyx.com/sign-up) with API key

### Install & Run

```bash
# Configure
cp .env.example .env
# Edit .env with your real credentials

# Install
pip install -r requirements.txt

# Run
python app.py
```

### Docker

```bash
docker build -t sms-two-factor-auth .
docker run --env-file .env -p 5000:5000 sms-two-factor-auth
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `OTP_EXPIRY_SECONDS` | Otp Expiry Seconds | No |
| `TELNYX_PHONE_NUMBER` | Phone number in E.164 format | Yes |
| `FLASK_DEBUG` | Flask Debug | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/request-otp` | `POST` /auth/request-otp |
| `POST` | `/auth/verify-otp` | `POST` /auth/verify-otp |
| `GET` | `/auth/otp-status` | Update status |

## Testing

**List records:**

```bash
curl http://localhost:5000/auth/otp-status
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
