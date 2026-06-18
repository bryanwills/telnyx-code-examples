# Build a Fax-to-Structured-Data Pipeline

Fax-to-Structured-Data Pipeline — receive faxes, AI extracts structured data (invoices, orders, prescriptions) into JSON.

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
           ├──► Telnyx Messaging (MMS)
           │
           ├──► Data extraction
           │
           ▼
     JSON response
```

## Telnyx Products Used

- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Webhook Events

Your app receives webhook events from Telnyx as things happen.

This app handles these webhook events:
- `fax.received` — Inbound fax received — media URL available

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/fax-to-structured-data-pipeline-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (70 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`receive_fax()`** — Processes receive fax request and returns result.
- **`extract_data()`** — Processes receive fax request and returns result.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/fax` | Telnyx webhook handler |
| `POST` | `/extract` | Extract Data |
| `GET` | `/faxes` | List Faxes |
| `GET` | `/extracted` | List Extracted |
| `GET` | `/health` | Health check |


The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    event_type = data.get("event_type", "")
    if event_type == "fax.received":
        fax_entry = {"fax_id": data.get("fax_id"), "from": data.get("from"), "to": data.get("to"),
            "pages": data.get("page_count"), "media_url": data.get("media_url"), "status": "received",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        fax_queue.append(fax_entry)
        return jsonify({"status": "queued", "fax_id": fax_entry["fax_id"]}), 200
    return jsonify({"status": "ok"}), 200

@app.route("/extract", methods=["POST"])
def extract_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid request body"}), 400
```

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=600):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.1}, timeout=20)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/webhooks/fax", methods=["POST"])
def receive_fax():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "invalid request body"}), 400
    data = payload.get("data", {})
    event_type = data.get("event_type", "")
    if event_type == "fax.received":
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
curl -X POST http://localhost:5000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/faxes | python3 -m json.tool
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
docker build -t fax-to-structured-data-pipeline-python .
docker run --env-file .env -p 5000:5000 fax-to-structured-data-pipeline-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
