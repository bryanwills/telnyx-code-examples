# Build a Edge Compliance Monitor

Real-time compliance checking for regulated call centers at the edge. AI monitors call transcriptions against TCPA, HIPAA, and PCI rules. Whispers warnings to agents before violations occur.

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
- `call.speak.ended` -- TTS playback finished, transitions to next action
- `call.hangup` -- Call ended, cleans up session state and logs outcome

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-compliance-monitor-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (150 lines). Here is what each piece does.


**`check_compliance()`** -- Check Compliance.

```python
def check_compliance(utterance, context):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=10, json={
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": f"Call context: {context}\nAgent utterance: {utterance}"}],
            "response_format": {"type": "json_object"}
        })
        if resp.ok:
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
```

**`handle_voice()`** -- Handle Voice.

```python
def handle_voice():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    ep = event.get("payload", {})
    cc_id = ep.get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.initiated" and ep.get("direction") == "incoming":
```

**`get_violations()`** -- Get Violations.

```python
def get_violations():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"violations": violations_log[-limit:], "total": len(violations_log)})
```

**`active_calls()`** -- Active Calls.

```python
def active_calls():
    return jsonify({"active": len(call_sessions),
                    "calls": {k: {"utterances": v.get("utterance_count", 0),
                                   "violations": len(v.get("violations", []))}
                              for k, v in call_sessions.items()}})
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/violations` | Violations |
| `GET` | `/calls` | Calls |
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
{"status": "ok", "service": "edge-compliance-monitor"}
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
