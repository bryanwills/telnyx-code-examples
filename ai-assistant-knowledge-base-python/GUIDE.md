# Build an AI Assistant Knowledge Base

AI Assistant Knowledge Base — AI Assistant with document knowledge base for context-aware Q&A over uploaded documents.

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
cd telnyx-code-examples/ai-assistant-knowledge-base-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (92 lines). Here's what each piece does.

### Business Logic

- **`chunk_text()`** — Processes chunk text request and returns result.
- **`get_embedding()`** — Makes an API call and processes the response.
- **`cosine_sim()`** — Processes cosine sim request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/documents` | Add Document |
| `POST` | `/ask` | Ask Question |
| `POST` | `/documents` | List Documents |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def add_document():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    title = data.get("title", f"doc-{int(time.time())}")
    content = data.get("content", "")
    if not content:
        return jsonify({"error": "content required"}), 400
    doc = {"id": len(documents), "title": title, "length": len(content),
        "chunks": 0, "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    text_chunks = chunk_text(content)
    for i, chunk in enumerate(text_chunks):
```

The main endpoint processes the request:

```python
def add_document():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    title = data.get("title", f"doc-{int(time.time())}")
    content = data.get("content", "")
    if not content:
        return jsonify({"error": "content required"}), 400
    doc = {"id": len(documents), "title": title, "length": len(content),
        "chunks": 0, "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
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
curl -X POST http://localhost:5000/documents \
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
docker build -t ai-assistant-knowledge-base-python .
docker run --env-file .env -p 5000:5000 ai-assistant-knowledge-base-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
