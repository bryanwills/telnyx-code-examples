# Build a Edge Webhook Aggregator

Multi-tenant webhook consolidation at the edge. Receives all Telnyx voice and messaging events, classifies by tenant from phone number mapping, batches events per interval, and forwards one consolidated payload per tenant.

## Telnyx Products Used

- **Edge Compute** -- run code at the network edge for low-latency processing
- **Voice** -- programmatic call control with webhooks for every call state change
- **Messaging** -- send and receive SMS programmatically

## API Endpoints

- See code for API calls

## Webhook Events

Telnyx uses webhooks for call control. You do not poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.



## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-webhook-aggregator-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (118 lines). Here is what each piece does.


**`flush_batches()`** -- Flush Batches.

```python
def flush_batches():
    """Flush accumulated events to tenant endpoints."""
    while True:
        time.sleep(BATCH_INTERVAL)
        with flush_lock:
            for tenant_id, events in list(event_batches.items()):
                if not events:
                    continue
                batch = events.copy()
                event_batches[tenant_id] = []
                endpoint = tenant_endpoints.get(tenant_id)
                if endpoint:
```

**`ingest_webhook()`** -- Ingest Webhook.

```python
def ingest_webhook():
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "No payload"}), 400
    event = payload.get("data", {})
    event_payload = event.get("payload", {})
    phone = event_payload.get("to", event_payload.get("from", ""))
    if isinstance(phone, list):
        phone = phone[0].get("phone_number", "") if phone else ""
    elif isinstance(phone, dict):
        phone = phone.get("phone_number", phone)
    tenant_id = tenant_map.get(phone, "unassigned")
```

**`register_tenant()`** -- Register Tenant.

```python
def register_tenant():
    data = request.get_json() or {}
    tenant_id = data.get("tenant_id")
    phones = data.get("phone_numbers", [])
    endpoint = data.get("callback_url")
    if not tenant_id or not endpoint:
        return jsonify({"error": "tenant_id and callback_url required"}), 400
    for phone in phones:
        tenant_map[phone] = tenant_id
    tenant_endpoints[tenant_id] = endpoint
    if tenant_id not in event_batches:
        event_batches[tenant_id] = []
```

**`list_tenants()`** -- List Tenants.

```python
def list_tenants():
    return jsonify({"tenants": {tid: {"endpoint": tenant_endpoints.get(tid, ""), "pending": len(event_batches.get(tid, []))}
                                for tid in tenant_endpoints}})
```

**`stats()`** -- Stats.

```python
def stats():
    return jsonify({"tenants": len(tenant_endpoints), "mapped_numbers": len(tenant_map),
                    "pending_events": sum(len(v) for v in event_batches.values())})
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/ingest` | Ingest |
| `POST` | `/tenants` | Tenants |
| `GET` | `/tenants` | Tenants |
| `GET` | `/stats` | Stats |
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
{"status": "ok", "service": "edge-webhook-aggregator"}
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
