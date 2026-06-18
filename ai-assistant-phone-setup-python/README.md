# Ai Assistant Phone Setup

AI Assistant Phone Setup — create and configure a managed Telnyx AI Assistant and wire it to a phone number.

## Telnyx Products Used

- AI Inference

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Manual assignment**

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
docker build -t ai-assistant-phone-setup .
docker run --env-file .env -p 5000:5000 ai-assistant-phone-setup
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/assistants` | Create new record |
| `GET` | `/assistants` | List all assistants |
| `GET` | `/assistants/<assistant_id>` | List all assistant |
| `PATCH` | `/assistants/<assistant_id>` | Update status |
| `POST` | `/assistants/<assistant_id>/wire` | `POST` /assistants/<assistant_id>/wire |
| `POST` | `/assistants/<assistant_id>/test` | `POST` /assistants/<assistant_id>/test |
| `GET` | `/models` | List all models |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/assistants
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/assistants \
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
