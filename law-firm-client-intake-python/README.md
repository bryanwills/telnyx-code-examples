# Law Firm Client Intake

AI answers after-hours calls, screens case type, collects facts, runs conflict check, books consultation via Calendly, collects retainer deposit via Stripe.

## Telnyx Products Used

- AI Inference
- SMS/MMS Messaging
- Speech Recognition / DTMF
- Text-to-Speech
- Voice Call Control

## Integrations

| Service | Purpose |
|---------|---------|
| **Stripe** | Payment processing, refunds, and checkout sessions |
| **Slack** | Team notifications and approval workflows |
| **Calendly** | Appointment scheduling |

## Human-in-the-Loop

This example includes human oversight at key decision points:

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
                                          ├──► Stripe
                                          ├──► Slack
                                          ├──► Calendly
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
- A Stripe account (for stripe integration)
- A Slack account (for slack integration)
- A Calendly account (for calendly integration)

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
docker build -t law-firm-client-intake .
docker run --env-file .env -p 5000:5000 law-firm-client-intake
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
| `MAIN_NUMBER` | Telnyx phone number in E.164 format (e.g., `+12345678901`) | Yes |
| `CONNECTION_ID` | Telnyx Call Control connection ID | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `STRIPE_API_KEY` | Stripe secret key for payment processing | Yes |
| `CALENDLY_TOKEN` | Calendly personal access token | Yes |
| `ATTORNEY_SLACK_WEBHOOK` | Slack incoming webhook URL for attorney notifications | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/intakes` | List all intakes |
| `POST` | `/intakes/<int:idx>/accept` | Accept and schedule (triggers confirmation) |
| `POST` | `/intakes/<int:idx>/decline` | Reject/deny a pending item (triggers customer notification) |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/intakes
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/intakes/<int:idx>/accept \
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
