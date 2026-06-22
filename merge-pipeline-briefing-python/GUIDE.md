# Build a Merge Pipeline Briefing

Morning pipeline briefing. Pulls rep pipeline from CRM via Merge. AI generates spoken briefing covering total deals, value, deals closing this week, and stale opportunities. Calls rep with personalized briefing.

## Telnyx Products Used

- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure

## API Endpoints

- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
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
cd telnyx-code-examples/merge-pipeline-briefing-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (298 lines). Here is what each piece does.


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

**`build_pipeline_summary()`** -- Build Pipeline Summary.

```python
def build_pipeline_summary(deals):
    """Analyze deals and build pipeline summary."""
    today = time.strftime("%Y-%m-%d")
    week_from_now = time.strftime("%Y-%m-%d", time.localtime(time.time() + 7 * 86400))
    stale_cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - STALE_DAYS * 86400))
    total_value = sum(float(d.get("amount") or 0) for d in deals)
    closing_soon = [
        d for d in deals
        if d.get("close_date") and today <= d["close_date"][:10] <= week_from_now
    ]
    stale = []
    for d in deals:
```

**`generate_briefing()`** -- Generate Briefing.

```python
def generate_briefing(summary):
    """Use AI to generate spoken pipeline briefing."""
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
```

**`trigger_briefing()`** -- Trigger Briefing.

```python
def trigger_briefing():
    """Trigger a pipeline briefing call."""
    data = request.get_json() or {}
    phone = data.get("phone")
    rep_name = data.get("rep_name", "")
    owner_id = data.get("owner_id")
    if not phone:
        return jsonify({"error": "phone required"}), 400
    # Pull pipeline from CRM
    params = {"page_size": 100}
    if owner_id:
        params["owner_id"] = owner_id
```

**`preview_briefing()`** -- Preview Briefing.

```python
def preview_briefing():
    """Preview briefing without calling — returns text and summary."""
    data = request.get_json() or {}
    owner_id = data.get("owner_id")
    params = {"page_size": 100}
    if owner_id:
        params["owner_id"] = owner_id
    pipeline = merge_get("/crm/v1/opportunities", params=params)
    deals = (pipeline or {}).get("results", [])
    summary = build_pipeline_summary(deals)
    briefing_text = generate_briefing(summary)
    return jsonify({"summary": summary, "briefing_text": briefing_text})
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
| `POST` | `/briefing` | Briefing |
| `POST` | `/briefing/preview` | Preview |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/briefings` | Briefings |
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
{"status": "ok", "service": "merge-pipeline-briefing"}
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
