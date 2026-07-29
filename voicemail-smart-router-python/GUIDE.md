# Build an AI Voicemail Smart Router

AI Voicemail Smart Router — transcribe voicemails, classify intent (urgent, billing, support, sales, spam, routine), and route to the right channel via Telnyx STT + AI Inference.

## How It Works

```
  Voicemail (audio or transcript)
        │
        ▼
  ┌──────────────────────────┐
  │ Your App                 │
  └────────┬─────────────────┘
           │
           ├──► Telnyx STT (audio → text)
           │
           ├──► Telnyx AI Inference (classify intent)
           │
           ▼
     Route to channel
       ├── urgent  → Slack alert
       ├── billing → Email
       ├── support → Ticket queue
       ├── sales   → CRM lead
       ├── spam    → Blocklist + archive
       └── routine → Daily digest
```

## Telnyx Products Used

- **AI Inference (Audio Transcriptions)** — Speech-to-text via `distil-whisper/distil-large-v2`
- **AI Inference (Chat Completions)** — LLM classifies the voicemail intent

## API Endpoints

- **Audio Transcriptions**: `POST /v2/ai/audio/transcriptions` — [API reference](https://developers.telnyx.com/api/inference/create-transcription)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/voicemail-smart-router-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py`. Here's what each piece does.

### Two Modes

1. **Direct transcript (`POST /voicemails/transcript`)** — submit text, get classification + routing. No audio needed.
2. **Audio file (`POST /voicemails/process`)** — upload a WAV/MP3, transcribe via STT, classify, and route.

### Model Fallback

The app tries the primary model (`zai-org/GLM-5.2`) first. If it fails or times out, it automatically falls back to `meta-llama/Llama-3.3-70B-Instruct`. Both are fast non-reasoning models that respond in 1-3 seconds.

### Routing Categories

| Category | Route | Destination |
|----------|-------|-------------|
| `urgent` | Slack | `#oncall-alerts` |
| `billing` | Email | `billing@company.com` |
| `support` | Ticket | `support-queue` |
| `sales` | CRM | `sales-leads` |
| `spam` | Blocklist | `archive` |
| `routine` | Digest | `daily-digest` |

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/voicemails/transcript` | Classify + route a text transcript |
| `POST` | `/voicemails/process` | Upload audio → STT → classify → route |
| `GET` | `/voicemails` | List voicemails (filter by category) |
| `GET` | `/voicemails/<id>` | Get a specific voicemail |
| `GET` | `/routes` | List routing decisions |
| `GET` | `/health` | Health check |

The classification + routing logic:

```python
def classify_and_route(transcript, caller_number=None):
    result = call_inference([system_prompt, user_prompt])
    category = result.get("category", "routine")
    routing = ROUTING_MAP.get(category, ROUTING_MAP["routine"])
    result["route"] = routing["route"]
    result["routed_to"] = routing["destination"]
    if category == "urgent" and SLACK_WEBHOOK:
        requests.post(SLACK_WEBHOOK, json={"text": f"URGENT: {transcript}"})
    return result
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

## Step 4: Test It

**Classify a transcript:**

```bash
curl -X POST http://localhost:5000/voicemails/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript":"This is an emergency. Our production system is down.","caller_number":"+17177247292"}' | python3 -m json.tool
```

**Try different categories:**

```bash
curl -X POST http://localhost:5000/voicemails/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript":"I have a question about my latest invoice"}'

curl -X POST http://localhost:5000/voicemails/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Hi, I am interested in your API pricing for startups"}'

curl -X POST http://localhost:5000/voicemails/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Congratulations! You won a free iPhone. Press 1 to claim."}'
```

**Process an audio file:**

```bash
curl -X POST http://localhost:5000/voicemails/process \
  -F "file=@voicemail.wav" \
  -F "caller_number=+17177247292" | python3 -m json.tool
```

**List voicemails by category:**

```bash
curl "http://localhost:5000/voicemails?category=urgent" | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — persist voicemails and routing decisions in PostgreSQL or Redis
- **Real voicemail integration** — wire `POST /voicemails/process` to Telnyx voicemail webhooks
- **Slack integration** — set `SLACK_WEBHOOK` for real-time urgent alerts
- **Email integration** — connect to SendGrid/SES for billing route
- **Ticketing** — auto-create Jira/Zendesk tickets for support route
- **CRM** — push sales leads to Salesforce/HubSpot
- **Blocklist** — persist spam numbers and auto-reject future calls
- **Rate limiting** — protect your endpoints from abuse

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/voicemail-smart-router-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
