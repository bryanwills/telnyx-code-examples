# Build a Run LLM inference on Telnyx — OpenAI-compatible chat completions API

Application powered by Telnyx AI Inference. Built with Telnyx AI Inference, Migration, Number Porting, SMS/MMS.

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
cd telnyx-code-examples/run-llm-inference-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (115 lines). Here's what each piece does.

### Business Logic

- **`chat_completion()`** — Makes an API call and processes the response.
- **`simple_ask()`** — Processes simple ask request and returns result.
- **`chat_endpoint()`** — Processes simple ask request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/inference/chat` | Chat Endpoint |
| `POST` | `/inference/ask` | Ask Endpoint |
| `GET` | `/health` | Health check |

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def chat_completion(messages, model=None, max_tokens=500, temperature=0.7):
    """Send a chat completion request to Telnyx Inference API.

    The API is OpenAI-compatible — same request/response format, different endpoint.
    """
    response = requests.post(
        INFERENCE_URL,
        headers={
            "Authorization": f"Bearer {TELNYX_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or AI_MODEL,
            "messages": messages,
```

The trigger endpoint kicks off the workflow:

```python
def chat_endpoint():
    """HTTP endpoint for chat completions — pass through to Telnyx Inference."""
    data = request.get_json()
    if not data or "messages" not in data:
        return jsonify({"error": "Request body must include 'messages' array"}), 400

    try:
        result = chat_completion(
            messages=data["messages"],
            model=data.get("model"),
            max_tokens=data.get("max_tokens", 500),
            temperature=data.get("temperature", 0.7),
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
curl -X POST http://localhost:5000/inference/chat \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
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
docker build -t run-llm-inference-python .
docker run --env-file .env -p 5000:5000 run-llm-inference-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
