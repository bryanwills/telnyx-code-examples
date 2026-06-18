# Cdr Usage Analytics Dashboard

pull Call Detail Records, build usage analytics with cost breakdowns, peak-hour analysis, and AI-powered insights.

## Telnyx Products Used

- AI Inference
- MMS Media Handling

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
docker build -t cdr-usage-analytics-dashboard .
docker run --env-file .env -p 5000:5000 cdr-usage-analytics-dashboard
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELNYX_API_KEY` | Your Telnyx API key from [portal.telnyx.com](https://portal.telnyx.com) | Yes |
| `AI_MODEL` | AI model for inference (default: `moonshotai/Kimi-K2.6`) | No |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/cdrs` | List all cdrs |
| `GET` | `/analytics/summary` | `GET` /analytics/summary |
| `GET` | `/analytics/peak-hours` | `GET` /analytics/peak-hours |
| `GET` | `/analytics/top-routes` | `GET` /analytics/top-routes |
| `GET` | `/analytics/ai-insights` | `GET` /analytics/ai-insights |
| `GET` | `/analytics/daily` | `GET` /analytics/daily |
| `GET` | `/health` | Health check and service status |

## Testing

**List records:**

```bash
curl http://localhost:5000/cdrs
```

**Health check:**

```bash
curl http://localhost:5000/health
```

## Learn More

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
