# Build a Number Reputation Monitor

Number Reputation Monitor — track outbound number reputation, auto-rotate flagged numbers.

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
           ├──► Telnyx Number Management
           │
           ├──► Reputation warmup
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **List Phone Numbers**: `GET /v2/phone_numbers` — [API reference](https://developers.telnyx.com/api/numbers/list-phone-numbers)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/number-reputation-monitor-auto-rotate-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (58 lines). Here's what each piece does.

### Business Logic

- **`get_numbers()`** — Makes an API call and processes the response.
- **`analyze_health()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.
- **`scan_numbers()`** — Processes scan numbers request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/scan` | Scan Numbers |
| `GET` | `/health-report` | Health check |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def scan_numbers():
    numbers = get_numbers()
    results = []
    for num in numbers[:20]:
        phone = num.get("phone_number", "")
        health = number_health.get(phone, {"calls": 0, "complaints": 0, "answer_rate": 0.5})
        try:
            analysis = json.loads(analyze_health({**health, "number": phone}))
            number_health[phone] = {**health, "analysis": analysis, "last_scan": time.time()}
            if analysis.get("recommendation") == "rotate":
                rotation_log.append({"number": phone, "reason": analysis.get("reasoning", "flagged"), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")})
            results.append({"number": phone, "analysis": analysis})
```

Helper function that handles the core action:

```python
def analyze_health(number_data):
    messages = [{"role": "system", "content": "Analyze phone number health metrics. Return JSON: risk_level (healthy/warning/critical), recommendation (keep/rotate/retire), reasoning (string)."},
        {"role": "user", "content": json.dumps(number_data)}]
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": 150, "temperature": 0.2}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/scan", methods=["POST"])
def scan_numbers():
    numbers = get_numbers()
    results = []
    for num in numbers[:20]:
        phone = num.get("phone_number", "")
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
curl -X POST http://localhost:5000/scan \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": ["+12125551234"],
    "carrier": "Current Carrier"
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
docker build -t number-reputation-monitor-auto-rotate-python .
docker run --env-file .env -p 5000:5000 number-reputation-monitor-auto-rotate-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
