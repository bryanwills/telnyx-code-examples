# CDR Usage Analytics Dashboard

> Pull Call Detail Records, build usage analytics with cost breakdowns, peak-hour analysis, and AI-powered insights.

## What You'll Build

A production-ready **cdr usage analytics dashboard** built with Python, Flask, and AI Inference.

| | |
|---|---|
| **Lines of code** | 113 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | AI Inference |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/cdr-usage-analytics-dashboard-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (113 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/cdrs` | Cdrs |
| `GET` | `/analytics/summary` | Summary |
| `GET` | `/analytics/peak-hours` | Peak Hours |
| `GET` | `/analytics/top-routes` | Top Routes |
| `GET` | `/analytics/ai-insights` | Ai Insights |
| `GET` | `/analytics/daily` | Daily |
| `GET` | `/health` | Health check |

### Key Functions

- **`fetch_cdrs()`** — fetch cdrs
- **`get_cdrs()`** — get cdrs
- **`usage_summary()`** — usage summary
- **`peak_hours()`** — peak hours
- **`top_routes()`** — top routes
- **`ai_insights()`** — ai insights
- **`daily_breakdown()`** — daily breakdown
- **`health()`** — health

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X GET http://localhost:5000/cdrs \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Production Deployment

### Docker

```bash
docker build -t cdr-usage-analytics-dashboard-python .
docker run --env-file .env -p 5000:5000 cdr-usage-analytics-dashboard-python
```

### Makefile

```bash
make setup    # Install dependencies
make run      # Start the server
make docker   # Build and run in Docker
```

## Customize & Extend

- Replace in-memory storage with PostgreSQL or Redis for production
- Add authentication to your API endpoints
- Set up monitoring and alerting
- Deploy behind a reverse proxy (nginx, Caddy) with TLS

## Resources

- [Full source code and README](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
