# Ai Billing Dispute Resolution Agent

AI Billing Dispute Resolution Agent — handles billing questions with account lookup.

## Telnyx Products Used

- AI Inference
- Speech Recognition / DTMF

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Escalation to human agents**
- **Manual review queues**

## How It Works

1. Customer **calls** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Human reviews** via dashboard, Slack, or SMS reply
6. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (call)                                     │
                                          ├──► Telnyx AI Inference
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
docker build -t ai-billing-dispute-resolution-agent .
docker run --env-file .env -p 5000:5000 ai-billing-dispute-resolution-agent
```

### Expose Your Webhook

For local development, use [ngrok](https://ngrok.com) to expose your server:

```bash
ngrok http 5000
```

Then set your Telnyx webhook URL to the ngrok HTTPS URL:

- **Voice:** `https://<your-ngrok>.ngrok.io/webhooks/voice`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `BILLING_NUMBER` | Phone number in E.164 format | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/disputes` | List all disputes |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/disputes
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
