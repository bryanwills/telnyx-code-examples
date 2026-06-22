# Build a Number Lookup Lead Enrichment

Number Lookup Lead Enrichment — CNAM and carrier lookup to qualify and enrich sales leads.

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
           ├──► Telnyx Number Lookup
           │
           ▼
     Email
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure
- **Number Lookup** — phone number search, purchase, and configuration

## API Endpoints

- **Number Lookup**: `GET /v2/number_lookup/{phone}` — [API reference](https://developers.telnyx.com/api/number-lookup/lookup)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/number-lookup-lead-enrichment-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (63 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`lookup_number()`** — Makes an API call and processes the response.
- **`enrich_lead()`** — Processes enrich lead request and returns result.
- **`enrich_bulk()`** — Processes enrich lead request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/enrich` | Enrich Lead |
| `POST` | `/enrich/bulk` | Enrich Bulk |
| `GET` | `/health` | Health check |

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=200):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.3}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/enrich", methods=["POST"])
def enrich_lead():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    phone = data.get("phone_number")
    if not phone:
        return jsonify({"error": "phone_number required"}), 400
```

The trigger endpoint kicks off the workflow:

```python
def enrich_lead():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
    phone = data.get("phone_number")
    if not phone:
        return jsonify({"error": "phone_number required"}), 400
    lookup = lookup_number(phone)
    carrier = lookup.get("carrier", {})
    cnam = lookup.get("caller_name", {})
    enrichment = {"phone": phone, "carrier_name": carrier.get("name"), "carrier_type": carrier.get("type"), "caller_name": cnam.get("caller_name"), "line_type": lookup.get("phone_number", {}).get("type"), "country": lookup.get("country_code")}
    msgs = [{"role": "system", "content": "Score this lead based on phone data. Return JSON: lead_quality (hot/warm/cold), reasoning (string), is_mobile (boolean), is_voip (boolean), recommended_channel (sms/voice/email)."},
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
curl -X POST http://localhost:5000/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999",
    "name": "Acme Corp",
    "source": "website",
    "interest": "enterprise plan"
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

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/number-lookup-lead-enrichment-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
