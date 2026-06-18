# Build an AI Competitive Win/Loss Call Analyzer

AI Competitive Win/Loss Call Analyzer — analyze recorded sales calls for competitive intelligence.

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
  │ • Business logic   │
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
cd telnyx-code-examples/ai-competitive-win-loss-call-analyzer-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (52 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`analyze_call()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.
- **`get_insights()`** — Fetches insights by ID with full details.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/analyze` | Analyze Call |
| `GET` | `/insights` | Get Insights |
| `GET` | `/health` | Health check |


The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=600):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/analyze", methods=["POST"])
def analyze_call():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    transcript = data.get("transcript", "")
    outcome = data.get("outcome", "unknown")
    if not transcript:
```

The trigger endpoint kicks off the workflow:

```python
def analyze_call():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    transcript = data.get("transcript", "")
    outcome = data.get("outcome", "unknown")
    if not transcript:
        return jsonify({"error": "transcript required"}), 400
    msgs = [{"role": "system", "content": "Analyze this sales call for competitive intelligence. Return JSON: outcome (won/lost/pending), competitors_mentioned (list), competitor_strengths_cited (list of {competitor, strength}), competitor_weaknesses_cited (list of {competitor, weakness}), our_strengths (list), our_weaknesses (list), price_discussed (boolean), price_objection (boolean), decision_factors (list ranked by importance), rep_performance (1-10), win_loss_reason (string), recommendation (string for future calls)."},
        {"role": "user", "content": f"Outcome: {outcome}\n\nTranscript:\n{transcript}"}]
    analysis = call_inference(msgs)
    try:
```


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
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/insights | python3 -m json.tool
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
docker build -t ai-competitive-win-loss-call-analyzer-python .
docker run --env-file .env -p 5000:5000 ai-competitive-win-loss-call-analyzer-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
