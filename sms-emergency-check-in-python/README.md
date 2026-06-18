# Sms Emergency Check In

SMS Emergency Check-In — periodic wellness checks via SMS with escalation to emergency contacts.

## Telnyx Products Used

- MMS Media Handling
- SMS/MMS Messaging
- Verify API

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Escalation to human agents**

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Human reviews** via dashboard, Slack, or SMS reply
5. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
                                          │
                                          ▼
                                     Human Review
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
docker build -t sms-emergency-check-in .
docker run --env-file .env -p 5000:5000 sms-emergency-check-in
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `CHECK_IN_NUMBER` | Phone number in E.164 format | Yes |
| `EMERGENCY_CONTACT` | Emergency Contact | Yes |
| `MESSAGING_PROFILE_ID` | Messaging Profile Id | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/messaging` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/monitor` | Create new record |
| `POST` | `/check-in/send` | Trigger workflow execution |
| `POST` | `/check-in/escalate` | `POST` /check-in/escalate |
| `GET` | `/status` | List all status |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/status
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/monitor \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [SMS & MMS Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
