# Full Stack Ai Contact Center

Full-Stack AI Contact Center — complete contact center: IVR + queue + AI agent assist + recording + live analytics.

## Telnyx Products Used

- AI Inference
- Speech Recognition / DTMF

## How It Works

1. Customer **calls** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (call)                                     │
                                          ├──► Telnyx AI Inference
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
docker build -t full-stack-ai-contact-center .
docker run --env-file .env -p 5000:5000 full-stack-ai-contact-center
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
| `MAIN_NUMBER` | Telnyx phone number in E.164 format (e.g., `+12345678901`) | Yes |
| `CONNECTION_ID` | Telnyx Call Control connection ID | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents` | `POST` /agents |
| `GET` | `/dashboard` | Dashboard / analytics view |
| `GET` | `/queues` | List all queues |
| `GET` | `/recordings` | List all recordings |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/dashboard
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/agents \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
