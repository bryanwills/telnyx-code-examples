# Sip Trunking Failover Monitor

SIP Trunking Failover Monitor — health-check SIP connections, auto-failover, SMS alerts.

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
docker build -t sip-trunking-failover-monitor .
docker run --env-file .env -p 5000:5000 sip-trunking-failover-monitor
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `ALERT_NUMBER` | Phone number in E.164 format | Yes |
| `PRIMARY_SIP_CONNECTION_ID` | Primary Sip Connection Id | Yes |
| `BACKUP_SIP_CONNECTION_ID` | Backup Sip Connection Id | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/check` | `POST` /check |
| `GET` | `/status` | List all status |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/status
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/check \
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
