# Billing Anomaly Detector

> Billing Anomaly Detector — monitor usage and billing for anomalies, alert on cost spikes and unusual patterns.

## What You'll Build

A production-ready **billing anomaly detector** built with Python, Flask, and CDR, Migration, Number Porting, SMS/MMS.

| | |
|---|---|
| **Lines of code** | 79 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | CDR, Migration, Number Porting, SMS/MMS |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **List CDRs**: `GET /v2/reports/cdrs` — [API reference](https://developers.telnyx.com/api/call-detail-records/list-cdrs)
- **List MDRs**: `GET /v2/reports/mdrs` — [API reference](https://developers.telnyx.com/api/messaging-detail-records/get-messaging-detail-records)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/billing-anomaly-detector-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (79 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/config` | Config |
| `GET` | `/config` | Config |
| `POST` | `/check` | Check |
| `GET` | `/balance` | Balance |
| `GET` | `/alerts` | Alerts |
| `GET` | `/health` | Health check |

### Key Functions

- **`set_baselines()`** — set baselines
- **`get_baselines()`** — get baselines
- **`run_anomaly_check()`** — run anomaly check
- **`check_balance()`** — check balance
- **`list_alerts()`** — list alerts
- **`health()`** — health

## Step 3: Run

```bash
python app.py
```

Server starts on `http://localhost:5000`.

Expose your local server for Telnyx webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and configure it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Webhook → `https://<id>.ngrok.io/webhooks/sms`

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/config \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or send an SMS to your Telnyx number to trigger the messaging workflow.

## Production Deployment

### Docker

```bash
docker build -t billing-anomaly-detector-python .
docker run --env-file .env -p 5000:5000 billing-anomaly-detector-python
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
- [Messaging Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
