# Build a TeXML Voicemail Drop — leave pre-recorded voicemails at scale via TeXML

TeXML Voicemail Drop — leave pre-recorded voicemails at scale via TeXML.

## How It Works

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Call Control      │
  └────────┬─────────┘
           │
           ├──► TeXML
           │
           ▼
     Email
```

## Telnyx Products Used

- **Voice** — programmatic call control with webhooks for every call state change

## API Endpoints

- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` — [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **Call Control: Start Playback**: `POST /v2/calls/{id}/actions/playback_start` — [API reference](https://developers.telnyx.com/api/call-control/start-playback)
- **Create Call**: `POST /v2/calls` — [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Webhook Events

Telnyx uses webhooks for call control — you don't poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.machine.detection.ended` — Answering machine detection completed — human or machine result
- `call.playback.ended` — Audio file playback completed

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
cd telnyx-code-examples/texml-voicemail-drop-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (73 lines). Here's what each piece does.

### Handling Webhooks

This is the core of the app — a state machine driven by Telnyx webhook events. Each event triggers the next step:

**`handle_voice()`** — The voice webhook handler — the core state machine. Each Telnyx event triggers the next action in the call flow.

### Business Logic

- **`voicemail_drop()`** — Makes an API call and processes the response.
- **`list_drops()`** — Returns all drops with metadata and pagination.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/drop` | Voicemail Drop |
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/drops` | List Drops |
| `GET` | `/health` | Health check |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    ccid = payload.get("data", {}).get("call_control_id")
    if event_type == "call.machine.detection.ended":
        result = payload.get("data", {}).get("result", "")
        if result in ("machine", "greeting_ended"):
            requests.post(f"https://api.telnyx.com/v2/calls/{ccid}/actions/playback_start",
                headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                json={"audio_url": VOICEMAIL_AUDIO_URL}, timeout=10)
            for d in drops:
                if d.get("ccid") == ccid:
                    d["status"] = "message_playing"
        else:
            requests.post(f"https://api.telnyx.com/v2/calls/{ccid}/actions/hangup",
                headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}, json={}, timeout=10)
            for d in drops:
```

The trigger endpoint kicks off the workflow:

```python
def voicemail_drop():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    numbers = data.get("numbers", [])
    results = []
    for number in numbers:
        try:
            resp = requests.post("https://api.telnyx.com/v2/calls", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
                json={"to": number, "from": FROM_NUMBER, "connection_id": CONNECTION_ID, "answering_machine_detection": "detect_beep",
                    "webhook_url": request.host_url.rstrip("/", timeout=10) + "/webhooks/voice"}, timeout=10)
            ccid = resp.json().get("data", {}).get("call_control_id")
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
curl -X POST http://localhost:5000/drop \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

Or call your Telnyx number from any phone to trigger the full voice workflow.

**Check results:**

```bash
curl http://localhost:5000/drops | python3 -m json.tool
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
docker build -t texml-voicemail-drop-python .
docker run --env-file .env -p 5000:5000 texml-voicemail-drop-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
