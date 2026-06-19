# Build a Edge Fraud Firewall

Screen every inbound call at the edge. Runs number lookup, velocity checks, AI classification, and blocklist matching before your app sees the call. Legitimate calls pass through; fraud gets rejected with cause code.

## Telnyx Products Used

- **Edge Compute** -- run code at the network edge for low-latency processing
- **Number Lookup** -- real-time caller identity and fraud signals
- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Transfer**: `POST /v2/calls/{id}/actions/transfer` -- [API reference](https://developers.telnyx.com/api/call-control/transfer-call)
- **Call Control: Reject**: `POST /v2/calls/{id}/actions/reject` -- [API reference](https://developers.telnyx.com/api/call-control/reject-call)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Number Lookup**: `GET /v2/number_lookup/{phone}` -- [API reference](https://developers.telnyx.com/api/number-lookup/lookup-number)

## Webhook Events

Telnyx uses webhooks for call control. You do not poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.speak.ended` -- TTS playback finished, transitions to next action
- `call.hangup` -- Call ended, cleans up session state and logs outcome

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Call Control Application](https://portal.telnyx.com/call-control/applications)
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-fraud-firewall-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (168 lines). Here is what each piece does.


**`lookup_number()`** -- Lookup Number.

```python
def lookup_number(phone):
    """Check number reputation via Telnyx Number Lookup."""
    try:
        resp = requests.get(
            f"https://api.telnyx.com/v2/number_lookup/{phone}",
            headers=HEADERS, timeout=10
        )
        if resp.ok:
            return resp.json().get("data", {})
    except Exception as e:
        app.logger.error("Number lookup failed: %s", e)
    return {}
```

**`classify_caller()`** -- Classify Caller.

```python
def classify_caller(phone, lookup_data):
    """Use AI to classify caller risk based on lookup data."""
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": "You are a fraud detection system. Analyze caller data and respond with ONLY one word: CLEAN, SUSPICIOUS, or BLOCK."},
                         {"role": "user", "content": f"Caller: {phone}\nCarrier: {lookup_data.get('carrier', {}).get('name', 'unknown')}\nType: {lookup_data.get('carrier', {}).get('type', 'unknown')}\nCountry: {lookup_data.get('country_code', 'unknown')}"}]
        })
        if resp.ok:
            return resp.json()["choices"][0]["message"]["content"].strip().upper()
    except Exception as e:
        app.logger.error("Classification failed: %s", e)
```

**`handle_voice()`** -- Handle Voice.

```python
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    call_control_id = event.get("payload", {}).get("call_control_id")
    if not call_control_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.initiated":
        direction = event.get("payload", {}).get("direction")
```

**`get_blocklist()`** -- Get Blocklist.

```python
def get_blocklist():
    return jsonify({"blocklist": sorted(blocklist), "count": len(blocklist)})
```

**`add_to_blocklist()`** -- Add To Blocklist.

```python
def add_to_blocklist():
    data = request.get_json() or {}
    phone = data.get("phone")
    if not phone:
        return jsonify({"error": "phone required"}), 400
    blocklist.add(phone)
    return jsonify({"status": "added", "phone": phone})
```

**`stats()`** -- Stats.

```python
def stats():
    return jsonify({
        "active_screenings": len(call_screening),
        "blocklist_size": len(blocklist)
    })
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/blocklist` | Blocklist |
| `POST` | `/blocklist` | Blocklist |
| `GET` | `/stats` | Stats |
| `GET` | `/health` | Health |

## Step 3: Run It

```bash
python app.py
```

Server starts on `http://localhost:5000`. Expose for webhooks:

```bash
ngrok http 5000
```

## Step 4: Test It

```bash
curl http://localhost:5000/health
```

```json
{"status": "ok", "service": "edge-fraud-firewall"}
```

## Going to Production

- Replace in-memory state with Redis or a database
- Add authentication to API endpoints
- Set up monitoring and alerting
- Use a process manager: `gunicorn -w 4 app:app`
- Configure failover webhook URLs in Telnyx Portal

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Call Control quickstart](https://developers.telnyx.com/docs/voice/call-control)
- [AI Inference docs](https://developers.telnyx.com/docs/inference)
- [Telnyx Portal](https://portal.telnyx.com)

## Production Checklist

### Authentication and Security
- [ ] API key in environment variable, never in code
- [ ] HTTPS for all webhook endpoints
- [ ] Input validation on all endpoints
- [ ] Webhook signature verification

### Webhook Reliability
- [ ] Return 200 within 5 seconds
- [ ] Idempotent webhook handling
- [ ] Failover URL configured

### Error Handling
- [ ] Timeout on all outbound requests
- [ ] Retry with backoff for transient failures
- [ ] Graceful degradation when AI unavailable

### Observability
- [ ] Structured logging with call IDs
- [ ] Health check endpoint
- [ ] Latency tracking
