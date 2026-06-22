# Build a Video Webinar Recording Manager

Video Webinar Recording Manager — manage video room webinars with automatic recording, transcription, and clip extraction.

## How It Works

```
  Scheduled Timer
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
  │ • Summarization    │
  └────────┬─────────┘
           │ ◄──── conversation loop
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/video-webinar-recording-manager-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (75 lines). Here's what each piece does.

### Starting the Workflow

**`create_webinar()`** — Kicks off the main workflow. Validates the request, creates the record, and initiates the Telnyx API calls.

```python
data = request.get_json()
    try:
        resp = requests.post(f"{API}/rooms", headers=headers,
            json={"unique_name": data.get("title", f"webinar-{int(time.time())}"),
                "max_participants": data.get("max_participants", 100),
                "enable_recording": True}, timeout=15)
        result = resp.json()
        room_id = result.get("data", {}).get("id")
```

### Business Logic

- **`get_recordings()`** — Makes an API call and processes the response.
- **`transcribe_recording()`** — Makes an API call and processes the response.
- **`list_webinars()`** — Returns all webinars with metadata and pagination.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webinars` | Create Webinar |
| `GET` | `/webinars/<room_id>/recordings` | Get Recordings |
| `POST` | `/recordings/<recording_id>/transcribe` | Transcribe Recording |
| `POST` | `/webinars` | List Webinars |
| `GET` | `/recordings` | List Processed |
| `GET` | `/health` | Health check |

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Trigger the workflow:**

```bash
curl -X POST http://localhost:5000/webinars \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/webinars/<room_id>/recordings | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Prompt engineering** — tune the AI prompts for your specific domain and tone
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/video-webinar-recording-manager-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
