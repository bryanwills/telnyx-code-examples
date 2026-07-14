# Build an AI Error Explainer

AI Error Explainer — paste a stack trace, get a root-cause hypothesis, confidence, severity, and a suggested fix via Telnyx AI Inference.

## How It Works

```
  Stack trace
        │
        ▼
  ┌──────────────────┐
  │ Your App          │
  └────────┬─────────┘
           │
           ├──► Telnyx AI Inference
           │
           ├──► Diagnosis + fix suggestion
           │
           ▼
     Structured JSON
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
cd telnyx-code-examples/error-explainer-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py`. Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends the diagnosis prompt to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint. Handles reasoning models by allowing large `max_tokens` and stripping markdown fences from the output.
- **`build_explain_prompt()`** — Constructs the prompt that asks the LLM to act as a senior engineer diagnosing the error, returning structured JSON with root cause, severity, confidence, likely culprit, suggested fix, fix snippet, related errors, and a prevention tip.

### Business Logic

- **`explain_error()`** — Accepts a stack trace, asks the LLM to produce a structured diagnosis, and stores the result.
- **`list_analyses()`** — Returns the most recent 50 analyses.
- **`get_analysis()`** — Returns a single analysis by ID.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/explain` | Diagnose an error from a stack trace |
| `GET` | `/analyses` | List analyses |
| `GET` | `/analyses/<id>` | Get a specific analysis |
| `GET` | `/health` | Health check |

The inference helper sends the prompt to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=4000):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=40)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"].get("content")
    if content is None:
        raise ValueError("model returned no content (try a larger max_tokens or a non-reasoning model)")
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content
        content = content.rsplit("```", 1)[0]
        content = content.strip()
    return content
```

The explain endpoint diagnoses the error:

```python
@app.route("/explain", methods=["POST"])
def explain_error():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    stack_trace = data.get("stack_trace", "")
    if not stack_trace.strip():
        return jsonify({"error": "stack_trace field is required"}), 400
    language = data.get("language")
    context = data.get("context")
    prompt = build_explain_prompt(stack_trace, language, context)
    result = call_inference([
        {"role": "system", "content": "You are a senior software engineer who diagnoses errors from stack traces. Return JSON only."},
        {"role": "user", "content": prompt},
    ])
    analysis = json.loads(result)
    analysis["id"] = f"ex-{int(time.time())}"
    analyses[analysis["id"]] = analysis
    return jsonify(analysis), 200
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

**Explain an error:**

```bash
curl -X POST http://localhost:5000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "context": "Flask production server",
    "stack_trace": "Traceback (most recent call last):\n  File \"app.py\", line 42, in handle_request\n    resp = requests.post(url)\nrequests.exceptions.ConnectionError: HTTPSConnectionPool(host=api.example.com, port=443): Max retries exceeded"
  }'
```

**List analyses:**

```bash
curl http://localhost:5000/analyses | python3 -m json.tool
```

**Get a specific analysis:**

```bash
curl http://localhost:5000/analyses/ex-<id> | python3 -m json.tool
```

## Going to Production

This example uses in-memory storage for simplicity. For production:

- **Database** — replace the in-memory dict with PostgreSQL or Redis
- **Authentication** — add API key validation on your endpoints
- **Rate limiting** — protect your endpoints from abuse
- **CI integration** — pipe CI logs directly to `/explain` for automated diagnosis
- **Prompt engineering** — tune the prompt for your stack and error patterns
- **Slack integration** — post high-severity diagnoses to a Slack channel

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/error-explainer-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
