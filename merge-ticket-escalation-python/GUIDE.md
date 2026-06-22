# Build a Merge Ticket Escalation

Critical ticket fires a webhook from Merge Ticketing. Calls the on-call engineer with AI-generated context briefing. Engineer says connect me to bridge directly with the customer. Updates ticket status.

## Telnyx Products Used

- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Transfer**: `POST /v2/calls/{id}/actions/transfer` -- [API reference](https://developers.telnyx.com/api/call-control/transfer-call)
- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` -- [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
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
cd telnyx-code-examples/merge-ticket-escalation-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (325 lines). Here is what each piece does.


**`merge_get()`** -- Merge Get.

```python
def merge_get(path, params=None):
    try:
        resp = requests.get(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, params=params
        )
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
        resp = requests.patch(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, json={"model": data}
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge PATCH %s failed: %s", path, e)
    return None
```

**`call_inference()`** -- Call Inference.

```python
def call_inference(prompt, context):
    try:
        resp = requests.post(
            INFERENCE_URL,
            headers=HEADERS,
            timeout=15,
            json={
                "model": AI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
```

**`handle_ticket_webhook()`** -- Handle Ticket Webhook.

```python
def handle_ticket_webhook():
    """Merge Ticketing webhook — critical ticket triggers on-call phone alert."""
    data = request.get_json() or {}
    ticket_id = data.get("id", "")
    ticket = merge_get(f"/ticketing/v1/tickets/{ticket_id}") if ticket_id else data
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    priority = (ticket.get("priority") or "").upper()
    if priority not in CRITICAL_PRIORITIES:
        return jsonify({"status": "skipped", "reason": f"Priority {priority} below threshold"})
    if not ONCALL_NUMBER:
        return jsonify({"error": "ONCALL_NUMBER not configured"}), 500
```

**`manual_escalate()`** -- Manual Escalate.

```python
def manual_escalate():
    """Manually trigger an escalation for testing."""
    data = request.get_json() or {}
    subject = data.get("subject", "Test Critical Ticket")
    description = data.get("description", "Production database connection failures.")
    if not ONCALL_NUMBER:
        return jsonify({"error": "ONCALL_NUMBER not configured"}), 500
    esc_id = f"esc-{int(time.time())}"
    ticket_context = {"subject": subject, "priority": "CRITICAL", "description": description}
    call_sessions[esc_id] = {"ticket": ticket_context, "outcome": "pending", "ts": time.time()}
    ttl_cleanup(call_sessions)
    try:
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

    state = decode_state(ep.get("client_state", ""))
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/ticket` | Ticket |
| `POST` | `/escalate` | Escalate |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/tickets` | Tickets |
| `GET` | `/escalations` | Escalations |
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
{"status": "ok", "service": "merge-ticket-escalation"}
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
