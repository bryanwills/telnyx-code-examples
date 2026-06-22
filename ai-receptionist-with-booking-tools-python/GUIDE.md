# Build an AI Receptionist with Booking Tools

AI Receptionist with Booking Tools — AI Assistant with tool_use for real calendar booking actions.

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
           ├──► Appointment scheduling
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
cd telnyx-code-examples/ai-receptionist-with-booking-tools-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (86 lines). Here's what each piece does.

### Business Logic

- **`execute_tool()`** — Processes execute tool request and returns result.
- **`chat()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/chat` | Chat |
| `GET` | `/bookings` | List Bookings |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    messages = data.get("messages", [])
    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": "You are a friendly office receptionist with access to a real booking system. Use the tools to check availability and book appointments. Be helpful and concise."})
    payload = {"model": AI_MODEL, "messages": messages, "tools": TOOLS, "max_tokens": 300, "temperature": 0.5}
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=20)
    resp.raise_for_status()
    choice = resp.json()["choices"][0]
    msg = choice["message"]
```

The main endpoint processes the request:

```python
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    messages = data.get("messages", [])
    if not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": "You are a friendly office receptionist with access to a real booking system. Use the tools to check availability and book appointments. Be helpful and concise."})
    payload = {"model": AI_MODEL, "messages": messages, "tools": TOOLS, "max_tokens": 300, "temperature": 0.5}
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"}, json=payload, timeout=20)
    resp.raise_for_status()
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
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999",
    "name": "Jane Smith",
    "date": "2026-07-15",
    "time": "14:00",
    "service": "Consultation"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/bookings | python3 -m json.tool
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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/ai-receptionist-with-booking-tools-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
