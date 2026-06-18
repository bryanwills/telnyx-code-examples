# Branded Caller ID Manager

> Branded Caller ID Manager — register, manage, and verify branded calling profiles with STIR/SHAKEN attestation for higher answer rates.

## What You'll Build

A production-ready **branded caller id manager** built with Python, Flask, and Branded Calling, CNAM Lookup, Migration, Number Porting, Verify.

| | |
|---|---|
| **Lines of code** | 91 |
| **Time to build** | ~15 minutes |
| **Difficulty** | Intermediate |
| **Products** | Branded Calling, CNAM Lookup, Migration, Number Porting, Verify |

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) with webhook URL
- [ngrok](https://ngrok.com) for local webhook testing

## Telnyx APIs Used

- **Update Number**: `PATCH /v2/phone_numbers/{id}` — [API reference](https://developers.telnyx.com/api/numbers/update-phone-number)
- **CNAM Listing**: `POST /v2/cnam_requests` — [API reference](https://developers.telnyx.com/api/cnam/create-cnam-request)
- **Number Lookup**: `GET /v2/number_lookup/{phone_number}` — [API reference](https://developers.telnyx.com/api/number-lookup/lookup-number)

## Step 1: Clone & Configure

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/branded-caller-id-manager-python
cp .env.example .env
pip install -r requirements.txt
```

Open `.env` and fill in your credentials. Every variable has a comment explaining where to find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Code Walkthrough

The entire app is in `app.py` (91 lines). Here's how it's structured:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/brands` | Brands |
| `GET` | `/brands` | Brands |
| `POST` | `/campaigns` | Campaigns |
| `PUT` | `/numbers/<number>/caller-id` | Caller Id |
| `GET` | `/stir-shaken/status` | Status |
| `GET` | `/campaigns` | Campaigns |
| `GET` | `/health` | Health check |

### Key Functions

- **`create_brand()`** — create brand
- **`list_brands()`** — list brands
- **`create_campaign()`** — create campaign
- **`update_caller_id()`** — update caller id
- **`stir_shaken_status()`** — stir shaken status
- **`list_campaigns()`** — list campaigns
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

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

## Step 4: Test

```bash
# Health check
curl http://localhost:5000/health
```

```bash
# Trigger the main workflow
curl -X POST http://localhost:5000/brands \
  -H "Content-Type: application/json" \
  -d '{}'
```

Or call your Telnyx number from any phone to trigger the voice workflow.

## Production Deployment

### Docker

```bash
docker build -t branded-caller-id-manager-python .
docker run --env-file .env -p 5000:5000 branded-caller-id-manager-python
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
- [Call Control Guide](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
- [Community & Support](https://support.telnyx.com)
