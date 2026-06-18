# Sip Failover Routing

Production-ready SIP failover routing system with Flask and Telnyx.

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Manual assignment**

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
docker build -t sip-failover-routing .
docker run --env-file .env -p 5000:5000 sip-failover-routing
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `PRIMARY_SIP_IP` | Primary Sip Ip | Yes |
| `PRIMARY_SIP_PORT` | Primary Sip Port | No |
| `BACKUP_SIP_IP` | Backup Sip Ip | Yes |
| `BACKUP_SIP_PORT` | Backup Sip Port | No |
| `FLASK_DEBUG` | Flask Debug | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/call` | External webhook handler |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sip/connections` | List all connections |
| `POST` | `/sip/connections` | Create new record |
| `GET` | `/sip/connections/<connection_id>` | List all connection |
| `GET` | `/sip/health` | Health check and service status |
| `GET` | `/sip/failover-status` | Update status |
| `POST` | `/sip/assign-number` | Assign to a team member (triggers notifications) |

## Testing

**List records:**

```bash
curl http://localhost:5000/sip/connections
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/sip/connections \
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
