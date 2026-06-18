# Build a Click-to-Call WebRTC with AI Assist

Click-to-Call WebRTC with AI Assist — browser-based calling with real-time AI coaching sidebar.

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
  │ Gather Speech     │ ── STT transcription
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

- **Telephony Credentials**: `POST /v2/telephony_credentials` — [API reference](https://developers.telnyx.com/api/webrtc/create-telephony-credential)
- **AI Inference**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/click-to-call-webrtc-with-ai-assist-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your Telnyx credentials. Each variable links to where you find it in the [Telnyx Portal](https://portal.telnyx.com).

## Step 2: Understand the Code

Everything lives in `app.py` (72 lines). Here's what each piece does.

### Business Logic

- **`get_token()`** — Makes an API call and processes the response.
- **`get_coaching()`** — Makes an API call and processes the response.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Index |
| `POST` | `/webrtc/token` | Get Token |
| `POST` | `/coaching` | Get Coaching |
| `GET` | `/health` | Health check |

The trigger endpoint kicks off the workflow:

```python
def get_token():
    try:
        resp = requests.post("https://api.telnyx.com/v2/telephony_credentials", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"connection_id": os.getenv("CONNECTION_ID", timeout=10)}, timeout=10)
        if resp.ok:
            return jsonify(resp.json().get("data", {})), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Failed to create credential"}), 500

@app.route("/coaching", methods=["POST"])
def get_coaching():
```

The main endpoint processes the request:

```python
def index():
    return render_template_string(CLICK_TO_CALL_HTML)

@app.route("/webrtc/token", methods=["POST"])
def get_token():
    try:
        resp = requests.post("https://api.telnyx.com/v2/telephony_credentials", headers={"Authorization": f"Bearer {TELNYX_API_KEY}", "Content-Type": "application/json"},
            json={"connection_id": os.getenv("CONNECTION_ID", timeout=10)}, timeout=10)
        if resp.ok:
            return jsonify(resp.json().get("data", {})), 200
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
curl -X POST http://localhost:5000/webrtc/token \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+12125559999"
  }'
```

**Check results:**

```bash
curl http://localhost:5000/ | python3 -m json.tool
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
docker build -t click-to-call-webrtc-with-ai-assist-python .
docker run --env-file .env -p 5000:5000 click-to-call-webrtc-with-ai-assist-python

# Or Makefile
make setup && make run
```

## Resources

- [Source code and reference](./README.md)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)
