# Build an Update AI Assistant

Update an existing Telnyx AI Assistant's configuration, model, system prompt, and tools via the API.

## How It Works

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Telnyx AI         │
  │ Assistants API    │
  └────────┬─────────┘
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **AI Assistants** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **Update AI Assistant**: `PATCH /v2/ai/assistants/{id}` -- [API reference](https://developers.telnyx.com/api/ai/update-assistant)
- **Get AI Assistant**: `GET /v2/ai/assistants/{id}` -- [API reference](https://developers.telnyx.com/api/ai/get-assistant)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/update-ai-assistant-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (91 lines). Here's what each piece does.

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

## Key Code

The update endpoint patches an existing AI Assistant:

```python
def update_assistant(
    assistant_id: str,
    name: str = None,
    instructions: str = None,
    model: str = None,
    enabled_features: list = None,
) -> dict:
    """Update an AI assistant and return JSON-serializable response data."""
    # Build update payload with only provided fields
    update_params = {}
    
    if name is not None:
        update_params["name"] = name
async def update_assistant_endpoint(assistant_id: str, request: UpdateAssistantRequest):
    """HTTP endpoint to update an AI assistant."""
    try:
        result = update_assistant(
            assistant_id=assistant_id,
            name=request.name,
            instructions=request.instructions,
            model=request.model,
            enabled_features=request.enabled_features,
        )
        return result
        
    except telnyx.AuthenticationError:
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
docker build -t update-ai-assistant-python .
docker run --env-file .env -p 5000:5000 update-ai-assistant-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
