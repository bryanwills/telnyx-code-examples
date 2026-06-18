# Build a Number Lookup Fraud Screener

Number Lookup Fraud Screener — screen inbound calls/messages for fraud indicators using number lookup before connecting.

## How It Works

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx Number Lookup
           │
           ├──► Risk analysis
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **Number Lookup** — phone number search, purchase, and configuration

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)

## Webhook Events

Telnyx uses webhooks for call control — you don't poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)) ([Messaging docs](https://developers.telnyx.com/docs/api/v2/messaging)):
- `call.initiated` — New inbound or outbound call detected
- `message.received` — Inbound SMS/MMS received

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications) configured with your webhook URL
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/number-lookup-fraud-screener-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (105 lines). Here's what each piece does.

### Business Logic

- **`calculate_risk()`** — Processes calculate risk request and returns result.
- **`screen_number()`** — Makes an API call and processes the response.
- **`screen_inbound_call()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/screen/<number>` | Screen Number |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `POST` | `/blocklist` | Add To Blocklist |
| `POST` | `/blocklist` | List Blocklist |
| `GET` | `/screening-log` | Get Log |
| `GET` | `/health` | Health check |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    data = payload.get("data", {})
    if data.get("event_type") == "call.initiated" and data.get("direction") == "incoming":
        caller = data.get("from", "")
        if caller in blocked_numbers:
            screening_log.append({"number": caller, "action": "blocked", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            return jsonify({"action": "reject"}), 200
        try:
            resp = requests.get(f"{API}/number_lookup/{caller}", headers=headers,
                params={"type": "caller-name"}, timeout=5)
            lookup = resp.json().get("data", {})
            risk = calculate_risk(lookup)
            screening_log.append({"number": caller, "risk": risk, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            if risk["action"] == "block":
                blocked_numbers.add(caller)
```

The trigger endpoint kicks off the workflow:

```python
def add_to_blocklist():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    number = data.get("number")
    blocked_numbers.add(number)
    return jsonify({"status": "blocked", "number": number}), 200

@app.route("/blocklist", methods=["GET"])
def list_blocklist():
    return jsonify({"blocked": list(blocked_numbers)}), 200

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

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Trigger the workflow:**

```bash
curl -X POST http://localhost:5000/blocklist \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999",
    "transaction": "TXN-98234",
    "amount": 847.50,
    "merchant": "Electronics Store",
    "risk_score": 92
  }'
```

Or call your Telnyx number from any phone to trigger the full voice workflow.

**Check results:**

```bash
curl http://localhost:5000/screen/<number> | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Error recovery** — handle call failures gracefully with retry or SMS fallback
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Deploy

```bash
# Docker
docker build -t number-lookup-fraud-screener-python .
docker run --env-file .env -p 5000:5000 number-lookup-fraud-screener-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
