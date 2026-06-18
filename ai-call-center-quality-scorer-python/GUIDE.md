# Build an AI Call Center Quality Scorer

AI Call Center Quality Scorer — automatically score agent performance from call recordings on compliance, empathy, resolution, and talk-to-listen ratio.

## How It Works

```
  API Request
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
  │ • Escalation logic │
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
cd telnyx-code-examples/ai-call-center-quality-scorer-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (85 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`score_call()`** — Handles the score call logic.
- **`batch_score()`** — Handles the batch score logic.
- **`list_scorecards()`** — Handles the list scorecards logic.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/score` | Score Call |
| `POST` | `/score/batch` | Batch Score |
| `GET` | `/scorecards` | List Scorecards |
| `GET` | `/scorecards/summary` | Summary |
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
curl -X POST http://localhost:5000/score \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/scorecards | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict/list with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Prompt engineering** — tune the AI prompts for your specific domain and tone
- **Monitoring** — add structured logging and health check alerts
- **Rate limiting** — protect your endpoints from abuse

## Deploy

```bash
# Docker
docker build -t ai-call-center-quality-scorer-python .
docker run --env-file .env -p 5000:5000 ai-call-center-quality-scorer-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
