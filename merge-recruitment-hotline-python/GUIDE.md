# Build a Merge Recruitment Hotline

Job seekers call. AI asks what role they want, searches open positions in ATS via Merge, describes top matches conversationally, and submits applications on their behalf with SMS confirmation.

## Telnyx Products Used

- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure
- **Messaging** -- send and receive SMS programmatically

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Gather Using Speak**: `POST /v2/calls/{id}/actions/gather_using_speak` -- [API reference](https://developers.telnyx.com/api/call-control/gather-using-speak)
- **Call Control: Speak (TTS)**: `POST /v2/calls/{id}/actions/speak` -- [API reference](https://developers.telnyx.com/api/call-control/speak)
- **Call Control: Hangup**: `POST /v2/calls/{id}/actions/hangup` -- [API reference](https://developers.telnyx.com/api/call-control/hangup)
- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Send Message (SMS)**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)

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
- [Merge.dev account](https://app.merge.dev) with linked integration
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/merge-recruitment-hotline-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (365 lines). Here is what each piece does.


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

**`merge_post()`** -- Merge Post.

```python
def merge_post(path, data):
    try:
        resp = requests.post(
            f"{MERGE_BASE}{path}", headers=MERGE_HEADERS, timeout=10, json={"model": data}
        )
        if resp.ok:
            return resp.json()
    except Exception as e:
        app.logger.error("Merge POST %s failed: %s", path, e)
    return None
```

**`search_jobs()`** -- Search Jobs.

```python
def search_jobs(query):
    """Search open jobs in ATS."""
    result = merge_get("/ats/v1/jobs", params={"status": "OPEN", "page_size": 20})
    if not result:
        return []
    jobs = result.get("results", [])
    if not query:
        return jobs[:5]
    query_lower = query.lower()
    scored = []
    for job in jobs:
        name = (job.get("name") or "").lower()
```

**`describe_jobs()`** -- Describe Jobs.

```python
def describe_jobs(jobs):
    """Use AI to create spoken description of matching jobs."""
    job_list = []
    for i, j in enumerate(jobs, 1):
        name = j.get("name", "Untitled")
        dept = ""
        if isinstance(j.get("departments"), list) and j["departments"]:
            d = j["departments"][0]
            dept = d.get("name", "") if isinstance(d, dict) else str(d)
        loc = ""
        if isinstance(j.get("offices"), list) and j["offices"]:
            o = j["offices"][0]
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

**`list_jobs()`** -- List Jobs.

```python
def list_jobs():
    """List open positions from ATS."""
    result = merge_get("/ats/v1/jobs", params={"status": "OPEN", "page_size": 20})
    return jsonify(result or {"results": []})
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/jobs` | Jobs |
| `GET` | `/applications` | Applications |
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
{"status": "ok", "service": "merge-recruitment-hotline"}
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
