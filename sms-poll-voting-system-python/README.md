# Sms Poll Voting System

SMS Poll Voting System — text-to-vote polling with real-time results.

## Telnyx Products Used

- SMS/MMS Messaging

## How It Works

1. **API call** triggers the workflow
2. Telnyx **webhook** delivers the event to your app
3. App **takes action** (creates record, dispatches, notifies)
4. **Customer notified** of outcome via SMS

```
API Trigger ──────────────────────────► Your App
                                          │
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
docker build -t sms-poll-voting-system .
docker run --env-file .env -p 5000:5000 sms-poll-voting-system
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `POLL_NUMBER` | Phone number in E.164 format | Yes |
| `MESSAGING_PROFILE_ID` | Messaging Profile Id | Yes |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/messaging` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/polls` | Create new record |
| `POST` | `/polls/<pid>/broadcast` | `POST` /polls/<pid>/broadcast |
| `GET` | `/polls/<pid>/results` | `GET` /polls/<pid>/results |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/polls/<pid>/results
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/polls \
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
- [Telnyx Portal](https://portal.telnyx.com)
