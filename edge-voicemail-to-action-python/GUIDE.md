# Build a Edge Voicemail to Action

AI-powered voicemail triage at the edge. Transcribes voicemails, classifies them (urgent, routine, spam), and takes action: urgent triggers callback, routine goes to SMS digest, spam gets blocklisted.

## Telnyx Products Used

- **Edge Compute** -- run code at the network edge for low-latency processing
- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure
- **Messaging** -- send and receive SMS programmatically

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` -- [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **Call Control: Reject**: `POST /v2/calls/{id}/actions/reject` -- [API reference](https://developers.telnyx.com/api/call-control/reject-call)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Send Message (SMS)**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Create Outbound Call**: `POST /v2/calls` -- [API reference](https://developers.telnyx.com/api/call-control/create-call)

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
- [Phone number](https://portal.telnyx.com/numbers/my-numbers) with voice enabled
- [Call Control Application](https://portal.telnyx.com/call-control/applications)
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-voicemail-to-action-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (186 lines). Here is what each piece does.


**`classify_voicemail()`** -- Classify Voicemail.

```python
def classify_voicemail(transcript):
    try:
        resp = requests.post(INFERENCE_URL, headers=HEADERS, timeout=15, json={
            "model": AI_MODEL,
            "messages": [{"role": "system", "content": CLASSIFY_PROMPT},
                         {"role": "user", "content": transcript}],
            "response_format": {"type": "json_object"}
        })
        if resp.ok:
            return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        app.logger.error("Classification failed: %s", e)
```

**`call_oncall()`** -- Call Oncall.

```python
def call_oncall(voicemail_data):
    if not ONCALL_NUMBER:
        return
    try:
        summary = voicemail_data.get("summary", "urgent voicemail")
        caller = voicemail_data.get("from", "unknown")
        requests.post("https://api.telnyx.com/v2/calls", headers=HEADERS, timeout=10, json={
            "connection_id": os.getenv("TELNYX_CONNECTION_ID", ""),
            "to": ONCALL_NUMBER, "from": TELNYX_PHONE,
            "webhook_url": request.url_root.rstrip("/") + "/webhooks/oncall"
        })
        app.logger.info("Calling on-call for urgent voicemail from %s", caller)
```

**`send_digest()`** -- Send Digest.

```python
def send_digest():
    while True:
        time.sleep(3600)
        if not routine_queue:
            continue
        batch = routine_queue.copy()
        routine_queue.clear()
        digest_text = f"{len(batch)} voicemail(s):\n"
        for vm in batch[:20]:
            digest_text += f"- {vm.get('from', '?')}: {vm.get('summary', '')}\n"
        for recipient in DIGEST_RECIPIENTS:
            recipient = recipient.strip()
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
    caller = ep.get("from", "")

```

**`handle_oncall()`** -- Handle Oncall.

```python
def handle_oncall():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_type = event.get("event_type", "")
    cc_id = event.get("payload", {}).get("call_control_id")
    if not cc_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    if event_type == "call.answered":
        urgent = [v for v in voicemails if v.get("classification") == "urgent"]
```

**`get_voicemails()`** -- Get Voicemails.

```python
def get_voicemails():
    classification = request.args.get("classification")
    limit = request.args.get("limit", 50, type=int)
    filtered = [v for v in voicemails if not classification or v.get("classification") == classification]
    return jsonify({"voicemails": filtered[-limit:], "total": len(filtered)})
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Voice |
| `POST` | `/webhooks/oncall` | Oncall |
| `GET` | `/voicemails` | Voicemails |
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
{"status": "ok", "service": "edge-voicemail-to-action"}
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
