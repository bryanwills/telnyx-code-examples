# Build a Webhook Debugger AI Assistant

Webhook Debugger AI Assistant — catch, inspect, and debug Telnyx webhooks with AI explanations.

## How It Works

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx AI Inference
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
cd telnyx-code-examples/webhook-debugger-ai-assistant-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (58 lines). Here's what each piece does.

### Handling Webhooks

Webhook handlers process events from Telnyx:

**`catch_webhook()`** — Handles Telnyx webhook events. Routes each event type to the appropriate handler.

**`analyze_webhook()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`analyze_recent()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.
- **`view_log()`** — Processes view log request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/catch/<path:subpath>` | Catch Webhook |
| `GET` | `/analyze/<int:index>` | Analyze Webhook |
| `GET` | `/analyze/recent` | Analyze Recent |
| `GET` | `/log` | View Log |
| `GET` | `/health` | Health check |

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=300):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/catch/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
def catch_webhook(subpath=""):
    entry = {"method": request.method, "path": f"/catch/{subpath}", "headers": dict(request.headers),
        "body": request.get_json(silent=True) or request.data.decode("utf-8", errors="replace")[:5000],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "query": dict(request.args)}
    webhook_log.append(entry)
    if len(webhook_log) > 500:
        webhook_log.pop(0)
```

The trigger endpoint kicks off the workflow:

```python
def catch_webhook(subpath=""):
    entry = {"method": request.method, "path": f"/catch/{subpath}", "headers": dict(request.headers),
        "body": request.get_json(silent=True) or request.data.decode("utf-8", errors="replace")[:5000],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "query": dict(request.args)}
    webhook_log.append(entry)
    if len(webhook_log) > 500:
        webhook_log.pop(0)
    return jsonify({"status": "caught", "id": len(webhook_log) - 1}), 200

@app.route("/analyze/<int:index>", methods=["GET"])
def analyze_webhook(index):
    if index >= len(webhook_log):
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

**Check results:**

```bash
curl http://localhost:5000/catch/<path:subpath> | python3 -m json.tool
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
docker build -t webhook-debugger-ai-assistant-python .
docker run --env-file .env -p 5000:5000 webhook-debugger-ai-assistant-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
