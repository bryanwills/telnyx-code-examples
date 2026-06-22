# Build a Call Whisper & Screen Pop

Call Whisper & Screen Pop — whisper caller info to agent before connecting the call.

## How It Works

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Call Control      │
  └────────┬─────────┘
           │
           ├──► Number Lookup
           │
           ├──► Case / claim handling
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **Voice** — programmatic call control with webhooks for every call state change
- **Number Lookup** — phone number search, purchase, and configuration

## API Endpoints

- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)
- **Number Lookup**: `GET /v2/number_lookup/{phone}` — [API reference](https://developers.telnyx.com/api/number-lookup/lookup)

## Webhook Events

Telnyx uses webhooks for call control — you don't poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.answered` — Call connected — app begins interaction
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.initiated` — New inbound or outbound call detected
- `call.speak.ended` — TTS playback finished — app transitions to next action (gather, transfer, etc.)

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
cd telnyx-code-examples/call-whisper-screen-pop-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (97 lines). Here's what each piece does.

### Handling Webhooks

This is the core of the app — a state machine driven by Telnyx webhook events. Each event triggers the next step:

**`handle_voice()`** — The voice webhook handler — the core state machine. Each Telnyx event triggers the next action in the call flow.

### Business Logic

- **`lookup_caller()`** — Makes an API call and processes the response.
- **`add_contact()`** — Validates input and creates new contact.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `POST` | `/contacts` | Add Contact |
| `GET` | `/health` | Health check |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        caller = data.get("from", "unknown")
        caller_info = lookup_caller(caller)
        active_calls[ccid] = {"caller": caller, "info": caller_info, "state": "holding"}
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        call = active_calls.get(ccid)
        if call:
            client.calls.actions.speak(ccid, payload="One moment please while we connect you.", voice="female", language_code="en-US")
            try:
                agent_resp = requests.post("https://api.telnyx.com/v2/calls", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                    json={"to": AGENT_NUMBER, "from": MAIN_NUMBER, "connection_id": CONNECTION_ID}, timeout=10)
```

The trigger endpoint kicks off the workflow:

```python
def add_contact():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    phone = data.get("phone")
    contacts_db[phone] = {k: v for k, v in data.items() if k != "phone"}
    return jsonify({"status": "added"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "contacts": len(contacts_db), "active": len(active_calls)}), 200

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
curl -X POST http://localhost:5000/contacts \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

Or call your Telnyx number from any phone to trigger the full voice workflow.

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Error recovery** — handle call failures gracefully with retry or SMS fallback
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/call-whisper-screen-pop-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
