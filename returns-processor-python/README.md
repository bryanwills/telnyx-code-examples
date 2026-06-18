# Returns Processor

customer texts photo of defective item via MMS, AI evaluates damage, auto-approves low-value refunds via Stripe, escalates high-value to team lead.

## Telnyx Products Used

- AI Inference
- MMS Media Handling
- SMS/MMS Messaging

## Integrations

| Service | Purpose |
|---------|---------|
| **Stripe** | Payment processing, refunds, and checkout sessions |
| **Shopify** | Order lookup, cart recovery, and store webhooks |
| **Slack** | Team notifications and approval workflows |

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Approval workflows**
- **Escalation to human agents**
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
                                          ├──► Stripe
                                          ├──► Shopify
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
- A Stripe account (for stripe integration)
- A Shopify account (for shopify integration)
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
docker build -t returns-processor .
docker run --env-file .env -p 5000:5000 returns-processor
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
| `STRIPE_API_KEY` | Stripe secret key for payment processing | Yes |
| `SHOPIFY_STORE` | Shopify store name (your-store.myshopify.com) | Yes |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin API access token | Yes |
| `SUPPORT_SLACK_WEBHOOK` | Slack incoming webhook URL for support notifications | No |
| `AUTO_REFUND_THRESHOLD` | Maximum auto-refund amount in dollars (default: `50`) | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/sms` | Telnyx SMS/MMS webhook handler (inbound messages) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/returns` | List all returns |
| `POST` | `/returns/<int:idx>/approve` | Approve a pending item (triggers customer notification) |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/returns
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/returns/<int:idx>/approve \
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
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
