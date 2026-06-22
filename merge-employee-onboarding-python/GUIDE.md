# Build a Merge Employee Onboarding

New employee webhook from Merge HRIS triggers full provisioning: Telnyx phone number, AI voicemail greeting, welcome SMS with IT setup instructions, and IT ticket via Merge Ticketing.

## Telnyx Products Used

- **Voice** -- programmatic call control with webhooks for every call state change
- **AI Inference** -- LLM inference with OpenAI-compatible API, runs on Telnyx infrastructure
- **Messaging** -- send and receive SMS programmatically
- **Numbers** -- search, order, and manage phone numbers

## API Endpoints

- **AI Inference**: `POST /v2/ai/chat/completions` -- [API reference](https://developers.telnyx.com/api/inference/chat-completions)
- **Send Message (SMS)**: `POST /v2/messages` -- [API reference](https://developers.telnyx.com/api/messaging/send-message)
- **Search Available Numbers**: `GET /v2/available_phone_numbers` -- [API reference](https://developers.telnyx.com/api/numbers/list-available-phone-numbers)
- **Order Numbers**: `POST /v2/number_orders` -- [API reference](https://developers.telnyx.com/api/numbers/create-number-order)

## Webhook Events

Telnyx uses webhooks for call control. You do not poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.



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
cd telnyx-code-examples/merge-employee-onboarding-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (247 lines). Here is what each piece does.


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

**`provision_number()`** -- Provision Number.

```python
def provision_number(area_code=""):
    """Search for and order a Telnyx phone number."""
    params = {"filter[country_code]": "US", "filter[limit]": 1}
    if area_code:
        params["filter[national_destination_code]"] = area_code
    try:
        search = requests.get(
            "https://api.telnyx.com/v2/available_phone_numbers",
            headers=HEADERS,
            timeout=10,
            params=params,
        )
```

**`generate_voicemail_greeting()`** -- Generate Voicemail Greeting.

```python
def generate_voicemail_greeting(name, department):
    """Generate a personalized voicemail greeting via AI."""
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

**`send_welcome_sms()`** -- Send Welcome Sms.

```python
def send_welcome_sms(phone, name, new_number):
    """Send welcome SMS to new employee."""
    msg = (
        f"Welcome {name}! Your company phone number is {new_number}. "
        f"Check your email for IT setup instructions including laptop, badge, and account access."
    )
    try:
        requests.post(
            "https://api.telnyx.com/v2/messages",
            headers=HEADERS,
            timeout=10,
            json={"from": TELNYX_PHONE, "to": phone, "text": msg},
```

**`create_it_ticket()`** -- Create It Ticket.

```python
def create_it_ticket(name, start_date, department, employee_id):
    """Create IT setup ticket in Merge Ticketing."""
    ticket_data = {
        "name": f"New hire IT setup: {name}",
        "description": (
            f"Provision laptop, accounts, badge, and office access for {name}.\n"
            f"Department: {department}\n"
            f"Start date: {start_date}\n"
            f"Employee ID: {employee_id}\n\n"
            f"Checklist:\n"
            f"- [ ] Laptop ordered and configured\n"
            f"- [ ] Email and Slack accounts created\n"
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/hris` | Hris |
| `POST` | `/onboard` | Onboard |
| `GET` | `/onboardings` | Onboardings |
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
{"status": "ok", "service": "merge-employee-onboarding"}
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
