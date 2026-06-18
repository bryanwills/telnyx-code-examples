# Maintenance Request Dispatch

tenant texts issue, AI categorizes and estimates cost, auto-dispatches vendor for routine work, manager approves orders over $500 via SMS reply.

## Telnyx Products Used

- AI Inference
- MMS Media Handling
- SMS/MMS Messaging

## Integrations

| Service | Purpose |
|---------|---------|
| **Slack** | Team notifications and approval workflows |

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Approval workflows**
- **Manual review queues**

## How It Works

1. Customer **texts** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Human reviews** via dashboard, Slack, or SMS reply
6. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (SMS)                                      │
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
docker build -t maintenance-request-dispatch .
docker run --env-file .env -p 5000:5000 maintenance-request-dispatch
```

### Expose Your Webhook

For local development, use [ngrok](https://ngrok.com) to expose your server:

```bash
ngrok http 5000
```

Then set your Telnyx webhook URL to the ngrok HTTPS URL:

- **Messaging:** `https://<your-ngrok>.ngrok.io/webhooks/sms`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `MAIN_NUMBER` | Telnyx phone number in E.164 format (e.g., `+12345678901`) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `MANAGER_NUMBER` | Phone number in E.164 format | Yes |
| `MANAGER_SLACK_WEBHOOK` | Slack incoming webhook URL for manager notifications | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/sms` | Telnyx SMS/MMS webhook handler (inbound messages) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/work-orders` | List all work orders |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/work-orders
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [SMS & MMS Guide](https://developers.telnyx.com/docs/messaging)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
