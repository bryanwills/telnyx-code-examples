# Build a Fax to AI Document Processor

Fax to AI Document Processor — receive fax, AI extracts data, forwards structured summary.

## How It Works

```
  API Request
        │
        ▼
  ┌──────────────────┐
  │ Parse message     │
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ AI Inference      │
  │ • Classification / triage│
  │ • Summarization    │
  └────────┬─────────┘
           │ ◄──── conversation loop
           │
           └──► Email
```

## Telnyx Products Used

- **SMS/MMS** — send and receive messages with delivery receipts
- **AI Inference** — LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **Send Message**: `POST /v2/messages` — [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Webhook Events

Telnyx delivers inbound messages and status updates via webhooks to your server.

This app handles these webhook events:
- `fax.received` — Inbound fax received — media URL available

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with messaging enabled
- [Messaging Profile](https://portal.telnyx.com/messaging/profiles) with webhook URL
- [ngrok](https://ngrok.com) for exposing your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/fax-to-ai-document-processor-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (58 lines). Here's what each piece does.

### Helper Functions

- **`call_inference()`** — Sends conversation context to Telnyx AI Inference and returns the model's response. Uses the OpenAI-compatible chat completions endpoint.

### Business Logic

- **`handle_fax()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/fax` | Telnyx webhook handler |
| `GET` | `/faxes` | List Faxes |
| `GET` | `/health` | Health check |

The webhook handler is the core state machine. Each Telnyx event triggers the next action:

```python
    event_type = data.get("event_type")
    if event_type == "fax.received":
        fax_id = data.get("fax_id")
        from_number = data.get("from")
        media_url = data.get("media_url")
        pages = data.get("page_count", 0)
        messages = [{"role": "system", "content": "A fax has been received. Classify the document type and extract key data. Return JSON: document_type (invoice/contract/medical_form/prescription/legal/other), sender (string), summary (2-3 sentences), key_fields (object of extracted values), priority (low/normal/urgent), action_required (string or null)."},
            {"role": "user", "content": f"Fax from {from_number}, {pages} pages. Fax ID: {fax_id}"}]
        try:
            analysis = call_inference(messages)
            result = json.loads(analysis)
        except Exception:
            result = {"document_type": "unknown", "summary": f"Fax received from {from_number}, {pages} pages"}
        processed = {"fax_id": fax_id, "from": from_number, "pages": pages, "analysis": result, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
```

The inference helper sends conversation context to Telnyx AI and returns the response:

```python
def call_inference(messages, max_tokens=400):
    resp = requests.post(INFERENCE_URL, headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
        json={"model": AI_MODEL, "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}, timeout=15)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

@app.route("/webhooks/fax", methods=["POST"])
def handle_fax():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "invalid request body"}), 400
    data = payload.get("data", {})
    event_type = data.get("event_type")
    if event_type == "fax.received":
```

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`.

In a separate terminal, expose your server for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Messaging Profile** → Inbound Webhook → `https://<id>.ngrok.io/webhooks/sms`

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

Or text your Telnyx number to trigger the SMS workflow.

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

## Run

```bash
pip install -r requirements.txt
python app.py
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/fax-to-ai-document-processor-python/README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Messaging quickstart](https://developers.telnyx.com/docs/messaging)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
