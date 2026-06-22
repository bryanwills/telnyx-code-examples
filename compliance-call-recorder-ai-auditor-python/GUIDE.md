# Build a Compliance Call Recorder + AI Auditor

Compliance Call Recorder + AI Auditor — auto-record, batch-process with AI, flag violations, create tickets.

## How It Works

```
  Inbound Phone Call
        │
        ▼
  ┌──────────────────┐
  │ Answer + Greet    │ ── TTS welcome message
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Gather Speech     │ ── STT transcription
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ AI Inference      │
  │ • Risk analysis    │
  │ • Classification / triage│
  │ • Case / claim handling│
  └────────┬─────────┘
           │ ◄──── conversation loop
           │
           ▼
     Ticket / issue
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure
- **Cloud Storage** — S3-compatible object storage for archiving call recordings

## APIs Used

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Cloud Storage (S3-compatible)**: recordings are uploaded with the AWS S3 SDK (`boto3`) — `s3.put_object` against the regional endpoint `https://{region}.telnyxcloudstorage.com`. Authentication is S3 SigV4 with your Telnyx API key passed as **both** the access key and the secret key. See the [Cloud Storage quickstart](https://developers.telnyx.com/docs/cloud-storage/quick-start).

## Webhook Events

Telnyx uses webhooks for call control — you don't poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

This app handles these webhook events ([Call Control docs](https://developers.telnyx.com/docs/api/v2/call-control)):
- `call.answered` — Call connected — app begins interaction
- `call.hangup` — Call ended — app cleans up session, triggers post-call processing
- `call.initiated` — New inbound or outbound call detected
- `call.recording.saved` — Call recording saved — URL available for download/processing
- `call.transcription` — Real-time transcription chunk received

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
cd telnyx-code-examples/compliance-call-recorder-ai-auditor-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (213 lines). Here's what each piece does.

### Starting the Workflow

**`create_ticket()`** — Kicks off the main workflow. Validates the request, creates the record, and initiates the Telnyx API calls.

```python
    if not TICKET_WEBHOOK_URL:
        app.logger.info("No TICKET_WEBHOOK_URL, skipping ticket creation")
        return
    try:
        requests.post(
            TICKET_WEBHOOK_URL,
            json=violation_data,
            headers={"Content-Type": "application/json"},
```

### Handling Webhooks

This is the core of the app — a state machine driven by Telnyx webhook events. Each event triggers the next step:

**`handle_voice()`** — The voice webhook handler — the core state machine. Each Telnyx event triggers the next action in the call flow.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`audit_transcript()`** — Processes audit transcript request and returns result.
- **`store_recording()`** — Downloads the saved recording from Telnyx, then uploads it to Telnyx Cloud Storage with `boto3` (`s3.put_object`) against the regional `https://{region}.telnyxcloudstorage.com` endpoint. The S3 client authenticates with your Telnyx API key supplied as both the access key and the secret key. Skipped if `STORAGE_BUCKET` is unset.
- **`get_audit_results()`** — Fetches audit results by ID with full details.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Telnyx webhook handler |
| `GET` | `/audit/results` | Get Audit Results |
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

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

Or call your Telnyx number from any phone to trigger the full voice workflow.

**Check results:**

```bash
curl http://localhost:5000/audit/results | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Error recovery** — handle call failures gracefully with retry or SMS fallback
- **Prompt engineering** — tune the AI prompts for your specific domain and tone
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/compliance-call-recorder-ai-auditor-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Cloud Storage quickstart (S3-compatible)](https://developers.telnyx.com/docs/cloud-storage/quick-start)
- [Telnyx Portal](https://portal.telnyx.com)
