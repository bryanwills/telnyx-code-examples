# Build a Production-ready Flask webhook for handling inbound calls via Telnyx Voice API

Production-ready Flask webhook for handling inbound calls via Telnyx Voice API.

## How It Works

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Call Control      │
  └────────┬─────────┘
           │
           ├──► TTS
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **Migration**
- **Number Porting** — phone number search, purchase, and configuration
- **Voice** — programmatic call control with webhooks for every call state change

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` — [API reference](https://developers.telnyx.com/api/call-control/speak)

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
cd telnyx-code-examples/route-phone-calls-to-ai-agent-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (132 lines). Here's what each piece does.

### Handling Webhooks

This is the core of the app — a state machine driven by Telnyx webhook events. Each event triggers the next step:

**`handle_call_webhook()`** — Handles Telnyx webhook events. Routes each event type to the appropriate handler.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/call` | Telnyx webhook handler |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
        
        if not event_type or not call_control_id:
            return jsonify({"error": "Missing event_type or call_control_id"}), 400
        
        # Handle call.initiated event — inbound call received
        if event_type == "call.initiated":
            from_number = payload.get("data", {}).get("from", {}).get("phone_number")
            to_number = payload.get("data", {}).get("to", {}).get("phone_number")
            
            # Answer the call
            answer_call(call_control_id)
            
            # Play greeting message
            speak_to_call(
```

The main endpoint processes the request:

```python
def handle_call_webhook():
    """Webhook endpoint to handle inbound call events."""
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "invalid request body"}), 400
        
        if not payload:
            return jsonify({"error": "No payload received"}), 400
        
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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/route-phone-calls-to-ai-agent-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
