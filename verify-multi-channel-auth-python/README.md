# Verify Multi Channel Auth

Verify Multi-Channel Auth — multi-channel verification: SMS first, fallback to voice call, then WhatsApp. Cascading 2FA.

## Telnyx Products Used

- Verify API
- WhatsApp Business API

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Escalation to human agents**

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
docker build -t verify-multi-channel-auth .
docker run --env-file .env -p 5000:5000 verify-multi-channel-auth
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/verify/start` | `POST` /verify/start |
| `POST` | `/verify/check` | `POST` /verify/check |
| `POST` | `/verify/escalate/<vid>` | `POST` /verify/escalate/<vid> |
| `POST` | `/verify/cascade` | `POST` /verify/cascade |
| `GET` | `/verifications` | List all verifications |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/verifications
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/verify/start \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [WhatsApp Guide](https://developers.telnyx.com/docs/messaging/whatsapp)
- [Telnyx Portal](https://portal.telnyx.com)
