# Fax To Ai Document Processor

Fax to AI Document Processor — receive fax, AI extracts data, forwards structured summary.

## Telnyx Products Used

- AI Inference
- MMS Media Handling
- SMS/MMS Messaging

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Manual review queues**

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Human reviews** via dashboard, Slack, or SMS reply
6. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
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
docker build -t fax-to-ai-document-processor .
docker run --env-file .env -p 5000:5000 fax-to-ai-document-processor
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `FAX_NUMBER` | Phone number in E.164 format | Yes |
| `FORWARD_EMAIL` | Forward Email | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/fax` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/faxes` | List all faxes |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/faxes
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
