# Build a Merge Deal Desk Alerts

CRM webhook fires when a deal moves to negotiation or exceeds a revenue threshold. Calls VP Sales with AI-generated spoken briefing. VP can say connect me to warm-transfer to the account executive.

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
cd telnyx-code-examples/merge-deal-desk-alerts-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (311 lines). Here is what each piece does.


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

**`should_alert()`** -- Should Alert.

```python
def should_alert(deal):
    stage = (deal.get("stage") or deal.get("status") or "").lower().replace(" ", "_")
    amount = float(deal.get("amount") or 0)
    if stage in ALERT_STAGES:
        return True
    if amount >= DEAL_THRESHOLD:
        return True
    return False
```

**`handle_crm_webhook()`** -- Handle Crm Webhook.

```python
def handle_crm_webhook():
    """Merge CRM webhook — deal stage change triggers VP alert call."""
    data = request.get_json() or {}
    deal_id = data.get("id", "")
    deal = merge_get(f"/crm/v1/opportunities/{deal_id}") if deal_id else data
    if not deal:
        return jsonify({"error": "Deal not found"}), 404
    if not should_alert(deal):
        return jsonify({"status": "skipped", "reason": "Below threshold"})
    if not VP_SALES_NUMBER:
        return jsonify({"error": "VP_SALES_NUMBER not configured"}), 500
    deal_context = {
```

**`manual_alert()`** -- Manual Alert.

```python
def manual_alert():
    """Manually trigger a deal alert for testing."""
    data = request.get_json() or {}
    deal_name = data.get("deal_name", "Test Deal")
    amount = data.get("amount", 100000)
    stage = data.get("stage", "negotiation")
    if not VP_SALES_NUMBER:
        return jsonify({"error": "VP_SALES_NUMBER not configured"}), 500
    alert_id = f"alert-{int(time.time())}"
    deal_context = {"name": deal_name, "amount": amount, "stage": stage}
    call_sessions[alert_id] = {"deal": deal_context, "ts": time.time()}
    ttl_cleanup(call_sessions)
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
| `POST` | `/webhooks/crm` | Crm |
| `POST` | `/alert` | Alert |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/deals` | Deals |
| `GET` | `/alerts` | Alerts |
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
{"status": "ok", "service": "merge-deal-desk-alerts"}
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
