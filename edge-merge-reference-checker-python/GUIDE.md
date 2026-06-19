# Build a Edge Merge Reference Checker

ATS application reaches reference-check stage. Calls each reference. AI conducts structured 5-question interview, scores responses, updates ATS, SMS summary to hiring manager.

## Telnyx Products Used

- **Edge Compute** -- run code at the network edge for low-latency processing
- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure
- **Messaging** -- send and receive SMS programmatically

## API Endpoints

- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` -- [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Send Message (SMS)**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Create Outbound Call**: `POST /v2/calls` -- [API reference](https://developers.telnyx.com/api/call-control/create-call)

## Webhook Events

Telnyx uses webhooks for call control. You do not poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

- `call.answered` -- Call connected, app begins interaction with greeting
- `call.gather.ended` -- Caller input received (speech or DTMF), app processes response
- `call.speak.ended` -- TTS playback finished, transitions to next action
- `call.hangup` -- Call ended, cleans up session state and logs outcome

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications)
- [Merge.dev account](https://app.merge.dev) with linked integration
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-merge-reference-checker-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (208 lines). Here is what each piece does.


**`merge_get()`** -- Merge Get.

```python
def merge_get(path, params=None):
    try:
        resp = requests.get(f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, params=params)
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge GET %s failed: %s", path, e)
    return None
```

**`merge_patch()`** -- Merge Patch.

```python
def merge_patch(path, data):
    try:
        resp = requests.patch(f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, json={"model": data})
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge PATCH %s failed: %s", path, e)
    return None
```

**`score_reference()`** -- Score Reference.

```python
def score_reference(answers):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [
                {"role": "system", "content": "Score this reference check. Respond with JSON: {\"overall_score\": 1-5, \"strengths\": [list], \"concerns\": [list], \"recommendation\": \"strong yes|yes|neutral|no|strong no\", \"summary\": \"2 sentence summary\"}"},
                {"role": "user", "content": json.dumps(answers)}
            ],
            "response_format": {"type": "json_object"}
        })
        if resp.ok:
            return json.loads(resp.json()["choices"][0]["message"]["content"])
```

**`start_reference_check()`** -- Start Reference Check.

```python
def start_reference_check():
    data = request.get_json() or {}
    candidate_name = data.get("candidate_name", "the candidate")
    references = data.get("references", [])
    application_id = data.get("application_id", "")
    if not references:
        return jsonify({"error": "references array required (each with name and phone)"}), 400
    check_id = f"ref-{int(time.time())}"
    reference_reports[check_id] = {
        "id": check_id, "candidate": candidate_name, "application_id": application_id,
        "references": [], "status": "in_progress", "ts": time.time()
    }
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

    if event_type == "call.answered":
```

**`list_reports()`** -- List Reports.

```python
def list_reports():
    return jsonify({"reports": list(reference_reports.values())})
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/check` | Check |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/reports` | Reports |
| `GET` | `/reports/<check_id>` | <Check Id> |
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
{"status": "ok", "service": "edge-merge-reference-checker"}
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
- [Merge.dev API docs](https://docs.merge.dev)
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
