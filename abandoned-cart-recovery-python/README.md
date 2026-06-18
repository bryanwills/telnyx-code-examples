# Abandoned Cart Recovery

SMS 1h after abandon with incentive, AI voice call 24h later if no purchase. Integrates with Shopify webhooks and Stripe for discount codes.

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
| **Shopify** | Order lookup, cart recovery, and store webhooks |

## How It Works

1. Customer **calls or texts** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (call/SMS)                                 │
                                          ├──► Telnyx AI Inference
                                          ├──► Stripe
                                          ├──► Shopify
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
- A Shopify account (for shopify integration)

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
docker build -t abandoned-cart-recovery .
docker run --env-file .env -p 5000:5000 abandoned-cart-recovery
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
| `SHOPIFY_STORE` | Shopify store name (your-store.myshopify.com) | Yes |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin API access token | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/shopify/cart-abandoned` | Shopify abandoned checkout webhook |
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |
| `POST` | `/webhooks/shopify/order-created` | Shopify order creation webhook (recovery tracking) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/recovery/run-sms` | Trigger workflow execution |
| `POST` | `/recovery/run-calls` | Trigger workflow execution |
| `GET` | `/carts` | List all carts |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/carts
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/recovery/run-sms \
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
