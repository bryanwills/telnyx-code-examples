# Call Sentiment Live Escalation

Call Sentiment Live Escalation — monitor call transcripts in real-time. When negative sentiment or distress is detected, auto-escalate to a supervisor.

## Telnyx Products Used

- AI Inference
- SMS/MMS Messaging

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
docker build -t call-sentiment-live-escalation .
docker run --env-file .env -p 5000:5000 call-sentiment-live-escalation
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `SUPERVISOR_NUMBER` | Phone number in E.164 format | Yes |
| `CONNECTION_ID` | Telnyx Call Control connection ID | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/monitor` | `POST` /monitor |
| `POST` | `/transcript` | `POST` /transcript |
| `GET` | `/calls/<call_id>/sentiment` | `GET` /calls/<call_id>/sentiment |
| `GET` | `/escalations` | List all escalations |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/calls/<call_id>/sentiment
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/monitor \
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
