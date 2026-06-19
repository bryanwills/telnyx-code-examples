# Build a Edge IVR A/B Tester

A/B test different IVR flows at the edge. Randomly assigns callers to variants, tracks completion rates per variant, and auto-promotes the winner when statistical significance is reached.

## Telnyx Products Used

- **Edge Compute** -- run code at the network edge for low-latency processing
- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)

## Webhook Events

Telnyx uses webhooks for call control. You do not poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.gather.ended` -- Caller input received (speech or DTMF), app processes response
- `call.hangup` -- Call ended, cleans up session state and logs outcome

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-ivr-ab-tester-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (163 lines). Here is what each piece does.


**`get_variant()`** -- Get Variant.

```python
def get_variant(experiment_id):
    exp = experiments.get(experiment_id)
    if not exp:
        return "A"
    if exp.get("winner"):
        return exp["winner"]
    a_n = exp["variants"]["A"]["calls"]
    b_n = exp["variants"]["B"]["calls"]
    if a_n >= MIN_SAMPLE and b_n >= MIN_SAMPLE:
        a_rate = exp["variants"]["A"]["completions"] / max(a_n, 1)
        b_rate = exp["variants"]["B"]["completions"] / max(b_n, 1)
        pooled = (exp["variants"]["A"]["completions"] + exp["variants"]["B"]["completions"]) / (a_n + b_n)
```

**`create_experiment()`** -- Create Experiment.

```python
def create_experiment():
    data = request.get_json() or {}
    exp_id = data.get("id", f"exp-{int(time.time())}")
    experiments[exp_id] = {
        "id": exp_id, "created": time.time(),
        "variant_a_greeting": data.get("variant_a_greeting", "Press 1 for support, 2 for sales."),
        "variant_b_greeting": data.get("variant_b_greeting", "Tell me how I can help you today."),
        "variant_a_gather": data.get("variant_a_gather", "dtmf"),
        "variant_b_gather": data.get("variant_b_gather", "speech"),
        "winner": None,
        "variants": {"A": {"calls": 0, "completions": 0, "dropoffs": 0, "total_duration": 0},
                      "B": {"calls": 0, "completions": 0, "dropoffs": 0, "total_duration": 0}}
```

**`list_experiments()`** -- List Experiments.

```python
def list_experiments():
    return jsonify({"experiments": list(experiments.values())})
```

**`get_experiment()`** -- Get Experiment.

```python
def get_experiment(exp_id):
    exp = experiments.get(exp_id)
    if not exp:
        return jsonify({"error": "Not found"}), 404
    return jsonify(exp)
```

**`handle_voice()`** -- Handle Voice.

```python
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    cc_id = event.get("payload", {}).get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.initiated":
        if event.get("payload", {}).get("direction") == "incoming":
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/experiments` | Experiments |
| `GET` | `/experiments` | Experiments |
| `GET` | `/experiments/<exp_id>` | <Exp Id> |
| `POST` | `/webhooks/voice` | Voice |
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
{"status": "ok", "service": "edge-ivr-ab-tester"}
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
