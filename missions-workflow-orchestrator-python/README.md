# Missions Workflow Orchestrator

Missions Workflow Orchestrator — create and manage multi-step mission workflows using the Telnyx Missions API.

## Telnyx Products Used

- SMS/MMS Messaging
- Verify API

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
docker build -t missions-workflow-orchestrator .
docker run --env-file .env -p 5000:5000 missions-workflow-orchestrator
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/missions` | Create new record |
| `GET` | `/missions` | List all missions |
| `GET` | `/missions/<mission_id>` | List all mission |
| `POST` | `/missions/<mission_id>/tasks` | Create new record |
| `POST` | `/missions/<mission_id>/run` | Trigger workflow execution |
| `GET` | `/missions/<mission_id>/runs` | List all runs |
| `GET` | `/templates` | `GET` /templates |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/missions
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/missions \
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
