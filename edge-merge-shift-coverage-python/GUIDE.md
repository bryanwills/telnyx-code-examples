# Build a Edge Merge Shift Coverage

Manager texts need a closer tonight. Edge worker checks HRIS schedule via Merge, calls available employees in priority order, negotiates, confirms via SMS to both parties.

## Telnyx Products Used

- **Edge Compute** -- run code at the network edge for low-latency processing
- **Voice** -- programmatic call control with webhooks for every call state change
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
cd telnyx-code-examples/edge-merge-shift-coverage-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (201 lines). Here is what each piece does.


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

**`get_available_employees()`** -- Get Available Employees.

```python
def get_available_employees():
    result = merge_get("/hris/v1/employees", params={"employment_status": "ACTIVE", "page_size": 50})
    employees = (result or {}).get("results", [])
    available = []
    for emp in employees:
        phone = None
        for pn in emp.get("phone_numbers", []):
            if pn.get("value"):
                phone = pn["value"]
                break
        if phone:
            available.append({"id": emp.get("id"), "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip(), "phone": phone})
```

**`call_next_employee()`** -- Call Next Employee.

```python
def call_next_employee(shift_id):
    shift = shift_requests.get(shift_id)
    if not shift:
        return
    candidates = shift.get("candidates", [])
    idx = shift.get("current_idx", 0)
    if idx >= len(candidates):
        manager_phone = shift.get("manager_phone")
        if manager_phone:
            try:
                requests.post("https://api.telnyx.com/v2/messages", headers=HEADERS, timeout=10,
                              json={"from": TELNYX_PHONE, "to": manager_phone,
```

**`handle_sms()`** -- Handle Sms.

```python
def handle_sms():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    ep = event.get("payload", {})
    text = ep.get("text", "").strip().lower()
    sender = ep.get("from", {})
    if isinstance(sender, dict):
        sender = sender.get("phone_number", "")
    if "need" in text and ("closer" in text or "shift" in text or "cover" in text):
        shift_id = f"shift-{int(time.time())}"
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

**`list_shifts()`** -- List Shifts.

```python
def list_shifts():
    return jsonify({"shifts": list(shift_requests.values())})
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/sms` | Sms |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/shifts` | Shifts |
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
{"status": "ok", "service": "edge-merge-shift-coverage"}
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
