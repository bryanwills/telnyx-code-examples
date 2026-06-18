# Fraud Alert Verification

suspicious transaction triggers voice call to customer, verifies via DTMF, blocks or approves in real-time. Fraud team reviews edge cases via Slack.

## Telnyx Products Used

- SMS/MMS Messaging
- Speech Recognition / DTMF
- Text-to-Speech
- Voice Call Control

## Integrations

| Service | Purpose |
|---------|---------|
| **Slack** | Team notifications and approval workflows |

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Approval workflows**
- **Escalation to human agents**
- **Manual review queues**

## How It Works

1. Customer **calls or texts** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Human reviews** via dashboard, Slack, or SMS reply
5. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (call/SMS)                                 │
                                          ├──► Slack
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
- A Telnyx phone number with voice and/or messaging enabled
- A [Call Control Application](https://portal.telnyx.com/app#/call-control/applications) configured with your webhook URL
- A Slack account (for slack integration)

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
docker build -t fraud-alert-verification .
docker run --env-file .env -p 5000:5000 fraud-alert-verification
```

### Expose Your Webhook

For local development, use [ngrok](https://ngrok.com) to expose your server:

```bash
ngrok http 5000
```

Then set your Telnyx webhook URL to the ngrok HTTPS URL:

- **Voice:** `https://<your-ngrok>.ngrok.io/webhooks/voice`
- **Messaging:** `https://<your-ngrok>.ngrok.io/webhooks/sms`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `MAIN_NUMBER` | Telnyx phone number in E.164 format (e.g., `+12345678901`) | Yes |
| `CONNECTION_ID` | Telnyx Call Control connection ID | Yes |
| `FRAUD_SLACK_WEBHOOK` | Slack incoming webhook URL for fraud notifications | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |
| `POST` | `/webhooks/sms` | Telnyx SMS/MMS webhook handler (inbound messages) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/alerts/trigger` | Trigger workflow execution |
| `GET` | `/alerts` | List all alerts |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/alerts
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/alerts/trigger \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [SMS & MMS Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
