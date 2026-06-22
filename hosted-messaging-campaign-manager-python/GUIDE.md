# Build a Hosted Messaging Campaign Manager

Hosted Messaging Campaign Manager — manage hosted messaging campaigns with subscriber opt-in/out tracking and delivery analytics.

## How It Works

```
  Inbound SMS/MMS
        │
        ▼
  ┌──────────────────┐
  │ Telnyx Messaging  │
  │ • Campaign / drip logic│
  └────────┬─────────┘
           │
           └──► JSON response
```

## Telnyx Products Used

- **Migration**
- **Number Porting** — phone number search, purchase, and configuration
- **SMS/MMS** — send and receive messages with delivery receipts

## API Endpoints

- **Send Message**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **List Messaging Profiles**: `GET /v2/messaging_profiles` — [API reference](https://developers.telnyx.com/api/messaging-profiles/list-messaging-profiles)

## Webhook Events

Telnyx delivers inbound messages and status updates via webhooks to your server.

This app handles these webhook events ([Messaging docs](https://developers.telnyx.com/docs/api/v2/messaging)):
- `message.finalized` — Final delivery status for outbound message
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
cd telnyx-code-examples/hosted-messaging-campaign-manager-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (110 lines). Here's what each piece does.

### Starting the Workflow

**`create_campaign()`** — Kicks off the main workflow. Validates the request, creates the record, and initiates the Telnyx API calls.

```python
data = request.get_json()
    cid = f"CAMP-{int(time.time())}"
    campaigns[cid] = {"id": cid, "name": data.get("name"), "message": data.get("message"),
        "status": "draft", "sent": 0, "delivered": 0, "failed": 0, "opted_out": 0,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    return jsonify({"campaign_id": cid, "campaign": campaigns[cid]}), 200
@app.route("/subscribers", methods=["POST"])
```

### Business Logic

- **`add_subscribers()`** — Validates input and creates new subscribers.
- **`send_campaign()`** — Makes an API call and processes the response.
- **`handle_messaging()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/campaigns` | Create Campaign |
| `POST` | `/subscribers` | Add Subscribers |
| `POST` | `/campaigns/<cid>/send` | Send Campaign |
| `POST` | `/webhooks/messaging` | Telnyx webhook handler |
| `POST` | `/subscribers` | List Subscribers |
| `POST` | `/campaigns` | List Campaigns |
| `GET` | `/analytics` | Analytics |
| `GET` | `/health` | Health check |

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
curl -X POST http://localhost:5000/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "recipients": ["+12125559999"],
    "message": "Special offer: 20% off this week",
    "campaign_name": "summer-promo"
  }'
```

Or text your Telnyx number to trigger the SMS workflow.

**Check results:**

```bash
curl http://localhost:5000/analytics | python3 -m json.tool
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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/hosted-messaging-campaign-manager-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Messaging quickstart](https://developers.telnyx.com/docs/messaging)
- [Telnyx Portal](https://portal.telnyx.com)
