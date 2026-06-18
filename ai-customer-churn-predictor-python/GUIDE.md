# Build an AI Customer Churn Predictor

AI Customer Churn Predictor — analyze call/message patterns via Telnyx APIs, AI predicts churn risk and suggests interventions.

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
           ├──► Classification / triage
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
cd telnyx-code-examples/ai-customer-churn-predictor-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (76 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`predict_churn()`** — Processes predict churn request and returns result.
- **`batch_predict()`** — Processes batch predict request and returns result.
- **`predict_churn_internal()`** — Processes predict churn internal request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/predict` | Predict Churn |
| `POST` | `/predict/batch` | Batch Predict |
| `GET` | `/predictions` | List Predictions |
| `GET` | `/health` | Health check |

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=400):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/predict", methods=["POST"])
def predict_churn():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    customer = data
    prompt = f"""Analyze this customer's communication pattern for churn risk. Customer data:
- Monthly call volume trend: {customer.get('call_volumes', [])}
```

The trigger endpoint kicks off the workflow:

```python
def predict_churn():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    customer = data
    prompt = f"""Analyze this customer's communication pattern for churn risk. Customer data:
- Monthly call volume trend: {customer.get('call_volumes', [])}
- Monthly message volume trend: {customer.get('message_volumes', [])}
- Support tickets last 90 days: {customer.get('support_tickets', 0)}
- Account age months: {customer.get('account_age_months', 0)}
- Contract renewal in days: {customer.get('renewal_days', 'unknown')}
- Last login days ago: {customer.get('last_login_days', 0)}
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
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/predictions | python3 -m json.tool
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
docker build -t ai-customer-churn-predictor-python .
docker run --env-file .env -p 5000:5000 ai-customer-churn-predictor-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
