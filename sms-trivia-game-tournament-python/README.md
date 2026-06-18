# Sms Trivia Game Tournament

SMS Trivia Game Tournament — multi-player trivia via SMS. Players join, answer timed questions, scores tracked on a live leaderboard.

## Telnyx Products Used

- AI Inference
- SMS/MMS Messaging

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
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
docker build -t sms-trivia-game-tournament .
docker run --env-file .env -p 5000:5000 sms-trivia-game-tournament
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `TRIVIA_NUMBER` | Phone number in E.164 format | Yes |
| `MESSAGING_PROFILE_ID` | Messaging Profile Id | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/messaging` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/tournament/create` | Create new record |
| `POST` | `/tournament/<tid>/next` | `POST` /tournament/<tid>/next |
| `GET` | `/tournament/<tid>/leaderboard` | `GET` /tournament/<tid>/leaderboard |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/tournament/<tid>/leaderboard
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/tournament/create \
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
