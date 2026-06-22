# Build a SMS Emergency Check-In

SMS Emergency Check-In — periodic wellness checks via SMS with escalation to emergency contacts.

## How It Works

```
  Inbound SMS/MMS
        │
        ▼
  ┌──────────────────┐
  │ Telnyx Messaging  │
  │ • Escalation logic │
  └────────┬─────────┘
           │
           └──► SMS notification
```

## Telnyx Products Used

- **SMS/MMS** — send and receive messages with delivery receipts

## API Endpoints

- **Send Message**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)

## Webhook Events

Telnyx delivers inbound messages and status updates via webhooks to your server.

This app handles these webhook events ([Messaging docs](https://developers.telnyx.com/docs/api/v2/messaging)):
- `message.received` — Inbound SMS/MMS received

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
cd telnyx-code-examples/sms-emergency-check-in-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (83 lines). Here's what each piece does.

### Helper Functions

- **`send_sms()`** — Sends an SMS via the Telnyx Messaging API. Wraps the `POST /v2/messages` call with error handling.

### Business Logic

- **`add_monitored()`** — Validates input and creates new monitored.
- **`send_check_ins()`** — Delivers check ins via Telnyx API.
- **`handle_reply()`** — Processes inbound SMS reply and routes to correct thread.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/monitor` | Add Monitored |
| `POST` | `/check-in/send` | Send Check Ins |
| `POST` | `/webhooks/messaging` | Telnyx webhook handler |
| `POST` | `/check-in/escalate` | Escalate Missed |
| `GET` | `/status` | Get Status |
| `GET` | `/health` | Health check |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    data = payload.get("data", {})
    if data.get("event_type") != "message.received" or data.get("direction") != "inbound":
        return jsonify({"status": "ignored"}), 200
    from_number = data.get("from", {}).get("phone_number", "")
    text = data.get("text", "").strip().upper()
    person = monitored.get(from_number)
    if not person: return jsonify({"status": "unknown"}), 200
    if "OK" in text or "GOOD" in text or "FINE" in text or "SAFE" in text:
        person["status"] = "ok"
        person["last_check_in"] = time.time()
        person["missed_count"] = 0
        send_sms(from_number, "Great to hear! Stay safe.")
    elif "HELP" in text or "SOS" in text:
        person["status"] = "escalated"
```

The trigger endpoint kicks off the workflow:

```python
def add_monitored():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    phone = data.get("phone")
    monitored[phone] = {"name": data.get("name", ""), "emergency_contact": data.get("emergency_contact", EMERGENCY_CONTACT),
        "last_check_in": time.time(), "status": "ok", "missed_count": 0}
    return jsonify({"status": "monitoring", "phone": phone}), 200

@app.route("/check-in/send", methods=["POST"])
def send_check_ins():
    results = []
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
curl -X POST http://localhost:5000/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999",
    "message": "Urgent: action required",
    "priority": "high"
  }'
```

Or text your Telnyx number to trigger the SMS workflow.

**Check results:**

```bash
curl http://localhost:5000/status | python3 -m json.tool
```

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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sms-emergency-check-in-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Messaging quickstart](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
