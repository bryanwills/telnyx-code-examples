# Build a Media Stream Live Transcription

Media Stream Live Transcription — fork call audio to WebSocket for real-time transcription display.

## How It Works

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Call Control      │
  └────────┬─────────┘
           │
           ├──► STT
           ├──► Media Streaming
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **Media Streaming**
- **Migration**
- **Number Porting** — phone number search, purchase, and configuration
- **Voice** — programmatic call control with webhooks for every call state change

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` — [API reference](https://developers.telnyx.com/api/call-control/speak)

## Webhook Events

Telnyx uses webhooks for call control — you don't poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)) ([Messaging docs](https://developers.telnyx.com/docs/api/v2/messaging)):
- `call.answered` — Call connected — app begins interaction
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.initiated` — New inbound or outbound call detected
- `call.transcription` — Real-time transcription chunk received
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
cd telnyx-code-examples/media-stream-live-transcription-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (55 lines). Here's what each piece does.

### Handling Webhooks

This is the core of the app — a state machine driven by Telnyx webhook events. Each event triggers the next step:

**`handle_voice()`** — The voice webhook handler — the core state machine. Each Telnyx event triggers the next action in the call flow.

### Business Logic

- **`get_transcript()`** — Retrieves call transcript with speaker labels.
- **`list_transcripts()`** — Returns all transcripts with metadata and pagination.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/transcripts/<ccid>` | Get Transcript |
| `GET` | `/transcripts` | List Transcripts |
| `GET` | `/health` | Health check |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_streams[ccid] = {"caller": data.get("from"), "started": time.time()}
        transcripts[ccid] = []
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.transcription_start(ccid, language="en")
        client.calls.actions.speak(ccid, payload="This call is being transcribed in real time. Go ahead and speak.", voice="female", language_code="en-US")
        return jsonify({"status": "streaming"}), 200
    elif event_type == "call.transcription":
        text = data.get("transcription_data", {}).get("transcript", "")
        if text and ccid in transcripts:
            transcripts[ccid].append({"text": text, "time": time.time()})
```

The main endpoint processes the request:

```python
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "invalid request body"}), 400
    event_type = payload.get("data", {}).get("event_type")
    ccid = payload.get("data", {}).get("call_control_id")
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        active_streams[ccid] = {"caller": data.get("from"), "started": time.time()}
        transcripts[ccid] = []
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

**Check results:**

```bash
curl http://localhost:5000/transcripts/<ccid> | python3 -m json.tool
```

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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/media-stream-live-transcription-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [Telnyx Portal](https://portal.telnyx.com)
