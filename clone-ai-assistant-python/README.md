# Clone Ai Assistant

Production-ready Flask application for cloning AI Assistants via Telnyx.

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Human override capability**

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Human reviews** via dashboard, Slack, or SMS reply
5. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
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
docker build -t clone-ai-assistant .
docker run --env-file .env -p 5000:5000 clone-ai-assistant
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `FLASK_DEBUG` | Flask Debug | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/assistants/<assistant_id>` | List all assistant |
| `POST` | `/assistants/<assistant_id>/clone` | `POST` /assistants/<assistant_id>/clone |

## Testing

**List records:**

```bash
curl http://localhost:5000/assistants/<assistant_id>
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/assistants/<assistant_id>/clone \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
