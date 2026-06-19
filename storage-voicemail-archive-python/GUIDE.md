# Build a Storage Voicemail Archive

Storage Voicemail Archive — record voicemails to Telnyx Cloud Storage with search.

## How It Works

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Call Control      │
  └────────┬─────────┘
           │
           ├──► Cloud Storage
           ├──► Call Recording
           │
           ▼
     Email
```

## Telnyx Products Used

- **Cloud Storage** — S3-compatible object storage for recordings and media
- **Voice** — programmatic call control with webhooks for every call state change
- **Call Recording** — records the caller's message as an MP3

## Cloud Storage (S3-Compatible)

Telnyx Cloud Storage speaks the S3 protocol, so this app uses `boto3` rather than a REST endpoint. Point the client at the region endpoint and pass your Telnyx API key as **both** the access key and the secret key (see the [Cloud Storage quick start](https://developers.telnyx.com/docs/cloud-storage/quick-start)):

```python
s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{REGION}.telnyxcloudstorage.com",
    aws_access_key_id=TELNYX_API_KEY,
    aws_secret_access_key=TELNYX_API_KEY,
    region_name=REGION,
    config=Config(signature_version="s3v4"),
)
```

The region is read from `TELNYX_STORAGE_REGION` (default `us-central-1`; also `us-east-1`, `us-west-1`, `eu-central-1`). Uploading a recording is a single `put_object` call:

```python
s3.put_object(Bucket=STORAGE_BUCKET, Key=filename, Body=audio, ContentType="audio/mpeg")
```

## Webhook Events

Telnyx uses webhooks for call control — you don't poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)) ([Messaging docs](https://developers.telnyx.com/docs/api/v2/messaging)):
- `call.answered` — Call connected — app begins interaction
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.initiated` — New inbound or outbound call detected
- `call.recording.saved` — Call recording saved — URL available for download/processing
- `call.speak.ended` — TTS playback finished — app transitions to next action (gather, transfer, etc.)
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
cd telnyx-code-examples/storage-voicemail-archive-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (61 lines). Here's what each piece does.

### Handling Webhooks

This is the core of the app — a state machine driven by Telnyx webhook events. Each event triggers the next step:

**`handle_voice()`** — The voice webhook handler — the core state machine. Each Telnyx event triggers the next action in the call flow.

### Business Logic

- **`list_voicemails()`** — Returns stored voicemails with transcription status.
- **`search_voicemails()`** — Processes search voicemails request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/voicemails` | List Voicemails |
| `GET` | `/voicemails/search` | Search Voicemails |
| `GET` | `/health` | Health check |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    data = payload.get("data", {})
    if event_type == "call.initiated" and data.get("direction") == "incoming":
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
    elif event_type == "call.answered":
        client.calls.actions.speak(ccid, payload="Please leave your message after the beep.", voice="female", language_code="en-US")
        return jsonify({"status": "greeting"}), 200
    elif event_type == "call.speak.ended":
        client.calls.actions.record_start(ccid, format="mp3", channels="single", play_beep=True, max_length_secs=120)
        return jsonify({"status": "recording"}), 200
    elif event_type == "call.recording.saved":
        recording_url = data.get("recording_urls", {}).get("mp3", "")
        caller = data.get("from", {}).get("phone_number", "unknown") if isinstance(data.get("from"), dict) else data.get("from", "unknown")
        filename = f"voicemail-{int(time.time())}-{caller.replace('+','')}.mp3"
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
        client.calls.actions.answer(ccid)
        return jsonify({"status": "answering"}), 200
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
curl http://localhost:5000/voicemails | python3 -m json.tool
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

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [Cloud Storage Quick Start (S3-compatible)](https://developers.telnyx.com/docs/cloud-storage/quick-start)
- [Telnyx Portal](https://portal.telnyx.com)
