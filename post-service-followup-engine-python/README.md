# Post Service Followup Engine

after appointment, SMS satisfaction survey. Negative responses trigger AI voice callback to understand the issue, then creates ticket in Jira and alerts manager via Slack.

## Telnyx Products Used

- AI Inference
- SMS/MMS Messaging
- Speech Recognition / DTMF
- Text-to-Speech
- Voice Call Control

## Integrations

| Service | Purpose |
|---------|---------|
| **Slack** | Team notifications and approval workflows |
| **Jira** | Ticket creation and issue tracking |
| **HubSpot** | CRM contact updates |

## Human-in-the-Loop

This example includes human oversight at key decision points:

- **Manual review queues**

## How It Works

1. Customer **calls or texts** your Telnyx number
2. Telnyx **webhook** delivers the event to your app
3. **AI processes** the request using Telnyx Inference
4. App **takes action** (creates record, dispatches, notifies)
5. **Human reviews** via dashboard, Slack, or SMS reply
6. **Customer notified** of outcome via SMS

```
Customer ──► Telnyx Number ──► Webhook ──► Your App
  (call/SMS)                                 │
                                          ├──► Telnyx AI Inference
                                          ├──► Slack
                                          ├──► Jira
                                          ├──► HubSpot
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
- A Telnyx phone number with voice and/or messaging enabled
- A [Call Control Application](https://portal.telnyx.com/app#/call-control/applications) configured with your webhook URL
- A Slack account (for slack integration)
- A Jira account (for jira integration)
- A HubSpot account (for hubspot integration)

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
docker build -t post-service-followup-engine .
docker run --env-file .env -p 5000:5000 post-service-followup-engine
```

### Expose Your Webhook

For local development, use [ngrok](https://ngrok.com) to expose your server:

```bash
ngrok http 5000
```

Then set your Telnyx webhook URL to the ngrok HTTPS URL:

- **Voice:** `https://<your-ngrok>.ngrok.io/webhooks/voice`
- **Messaging:** `https://<your-ngrok>.ngrok.io/webhooks/sms`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `MAIN_NUMBER` | Telnyx phone number in E.164 format (e.g., `+12345678901`) | Yes |
| `CONNECTION_ID` | Telnyx Call Control connection ID | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |
| `JIRA_URL` | Jira instance URL (e.g., `https://yourco.atlassian.net`) | No |
| `JIRA_EMAIL` | Jira account email for API authentication | No |
| `JIRA_TOKEN` | Jira API token | No |
| `JIRA_PROJECT` | Jira project key for ticket creation (e.g., `SUP`) | No |
| `MANAGER_SLACK_WEBHOOK` | Slack incoming webhook URL for manager notifications | No |
| `HUBSPOT_API_KEY` | HubSpot private app access token | No |

## Webhook Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/sms` | Telnyx SMS/MMS webhook handler (inbound messages) |
| `POST` | `/webhooks/voice` | Telnyx voice webhook handler (call lifecycle events) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/follow-up/send` | Trigger workflow execution |
| `GET` | `/follow-ups` | List all followups |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/follow-ups
```

**Trigger action:**

```bash
curl -X POST http://localhost:5000/follow-up/send \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [SMS & MMS Guide](https://developers.telnyx.com/docs/messaging)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
