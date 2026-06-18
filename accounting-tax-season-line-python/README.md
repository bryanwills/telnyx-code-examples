# Accounting Tax Season Line

handles scheduling, document checklist reminders, status updates. AI texts clients with missing doc reminders. CPA reviews readiness before appointments.

## Telnyx Products Used

- AI Inference
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

- **Manual review queues**

## How It Works

1. Customer **calls or texts** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Human reviews** via dashboard, Slack, or SMS reply
6. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (call/SMS)                                 │
                                          ├──► Telnyx AI Inference
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
docker build -t accounting-tax-season-line .
docker run --env-file .env -p 5000:5000 accounting-tax-season-line
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
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `CPA_SLACK_WEBHOOK` | Slack incoming webhook URL for cpa notifications | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |
| `POST` | `/webhooks/sms` | Telnyx SMS/MMS webhook handler (inbound messages) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/reminders/send` | Trigger workflow execution |
| `GET` | `/clients` | List all clients |
| `POST` | `/clients/<int:idx>/doc-received` | Record document received |
| `GET` | `/readiness` | Dashboard / analytics view |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/clients
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/reminders/send \
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
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
