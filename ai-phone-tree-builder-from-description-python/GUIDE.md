# Build an AI Phone Tree Builder

AI Phone Tree Builder — describe your business in English, AI creates a working phone system.

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
cd telnyx-code-examples/ai-phone-tree-builder-from-description-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (66 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`generate_phone_tree()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/generate` | Generate Phone Tree |
| `GET` | `/health` | Health check |

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=800):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.5}, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/generate", methods=["POST"])
def generate_phone_tree():
    """Describe your business, get a complete AI Assistant + TeXML phone tree."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    description = data.get("description", "")
    if not description:
```

The trigger endpoint kicks off the workflow:

```python
def generate_phone_tree():
    """Describe your business, get a complete AI Assistant + TeXML phone tree."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    description = data.get("description", "")
    if not description:
        return jsonify({"error": "Provide a business description"}), 400

    messages = [{"role": "system", "content": """You are a phone system architect. Given a business description, generate:
1. A Telnyx AI Assistant configuration (JSON) with name, instructions, greeting, voice, and insight_settings
2. A TeXML document (XML) for fallback IVR routing
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
curl -X POST http://localhost:5000/generate \
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

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-phone-tree-builder-from-description-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
