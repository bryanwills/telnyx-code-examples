# Build a Missions AI Task Runner

Missions AI Task Runner — AI-driven task execution within the Telnyx Missions framework. AI decides next steps based on task results.

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
  │ Listen for Input  │
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
     SMS notification
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure
- **Number Lookup** — phone number search, purchase, and configuration

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/missions-ai-task-runner-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (76 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`run_ai_task()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/run` | Run Ai Task |
| `GET` | `/runs` | List Runs |
| `GET` | `/actions` | List Actions |
| `GET` | `/health` | Health check |

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=400):
    resp = requests.post(INFERENCE_URL, headers=headers,
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/run", methods=["POST"])
def run_ai_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    objective = data.get("objective", "")
    context = data.get("context", {})
    max_steps = data.get("max_steps", 5)
```

The trigger endpoint kicks off the workflow:

```python
def run_ai_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    objective = data.get("objective", "")
    context = data.get("context", {})
    max_steps = data.get("max_steps", 5)
    steps = []
    conversation = [{"role": "system", "content": f"You are a task execution AI. Available actions: {json.dumps(list(AVAILABLE_ACTIONS.keys()))}. Given an objective, plan and execute steps. For each step return JSON: action (string), params (object), reasoning (string). Return action='done' when objective is met."},
        {"role": "user", "content": f"Objective: {objective}\nContext: {json.dumps(context)}"}]
    for i in range(max_steps):
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
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/runs | python3 -m json.tool
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
docker build -t missions-ai-task-runner-python .
docker run --env-file .env -p 5000:5000 missions-ai-task-runner-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
