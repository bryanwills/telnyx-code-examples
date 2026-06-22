# Send MMS Picture Messages with Telnyx

Send an MMS message with image attachments using the Telnyx Messaging API.

## How It Works

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Telnyx Messaging  │
  └────────┬─────────┘
           │
           └──► JSON response
```

## Telnyx Products Used

- **Messaging** — send and receive messages with delivery receipts

## API Endpoints

- **Send Message**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/send-mms-picture-message-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (110 lines). Here's what each piece does.

### Business Logic

- **`send_mms_endpoint()`** — Delivers mms endpoint via Telnyx API.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/mms/send` | Send Mms Endpoint |

The trigger endpoint kicks off the workflow:

```python
def send_mms_endpoint():
    """HTTP endpoint to send MMS with media attachments."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    to_number = data.get("to")
    message = data.get("message")
    media_urls = data.get("media_urls", [])
```

The main endpoint processes the request:

```python
def send_mms_endpoint():
    """HTTP endpoint to send MMS with media attachments."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    to_number = data.get("to")
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

In a separate terminal, expose your server for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Webhook → `https://<id>.ngrok.io/webhooks/sms`

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Trigger the workflow:**

```bash
curl -X POST http://localhost:5000/mms/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

Or text your Telnyx number to trigger the SMS workflow.

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/send-mms-picture-message-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Messaging quickstart](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
