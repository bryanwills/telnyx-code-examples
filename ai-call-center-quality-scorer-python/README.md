# Ai Call Center Quality Scorer

AI Call Center Quality Scorer — automatically score agent performance from call recordings on compliance, empathy, resolution, and talk-to-listen ratio.

## Telnyx Products Used

- AI Inference

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Escalation to human agents**

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
docker build -t ai-call-center-quality-scorer .
docker run --env-file .env -p 5000:5000 ai-call-center-quality-scorer
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/score` | `POST` /score |
| `POST` | `/score/batch` | `POST` /score/batch |
| `GET` | `/scorecards` | List all scorecards |
| `GET` | `/scorecards/summary` | `GET` /scorecards/summary |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/scorecards
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/score \
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
