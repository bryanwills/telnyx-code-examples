# Build a Edge Number Masking

Marketplace-style proxy number pool at the edge. Dynamically assigns masked number pairs per booking, routes calls bidirectionally through the proxy, records for dispute resolution, and auto-expires at checkout.

## Telnyx Products Used

- **Edge Compute** -- run code at the network edge for low-latency processing
- **Numbers** -- search, order, and manage phone numbers
- **Voice** -- programmatic call control with webhooks for every call state change
- **Call Recording** -- record calls for compliance and quality

## API Endpoints

- **Call Control: Answer**: `POST /v2/calls/{id}/actions/answer` -- [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Call Control: Transfer**: `POST /v2/calls/{id}/actions/transfer` -- [API reference](https://developers.telnyx.com/api/call-control/transfer-call)
- **Call Control: Reject**: `POST /v2/calls/{id}/actions/reject` -- [API reference](https://developers.telnyx.com/api/call-control/reject-call)
- **Call Control: Record Start**: `POST /v2/calls/{id}/actions/record_start` -- [API reference](https://developers.telnyx.com/api/call-control/start-recording)

## Webhook Events

Telnyx uses webhooks for call control. You do not poll for state. Each event tells you what happened, and your response tells Telnyx what to do next.

- `call.initiated` -- New inbound or outbound call detected
- `call.answered` -- Call connected, app begins interaction with greeting
- `call.recording.saved` -- Recording available for download
- `call.hangup` -- Call ended, cleans up session state and logs outcome

## Prerequisites

- Python 3.8+
- [Telnyx account](https://portal.telnyx.com/sign-up) with funded balance
- [API key](https://portal.telnyx.com/api-keys)
- [ngrok](https://ngrok.com) for local webhook testing

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-number-masking-python
cp .env.example .env
pip install -r requirements.txt
```

Edit `.env` with your credentials.

## Step 2: Understand the Code

Everything lives in `app.py` (146 lines). Here is what each piece does.


**`ttl_cleanup_masks()`** -- Ttl Cleanup Masks.

```python
def ttl_cleanup_masks():
    now = time.time()
    expired = [k for k, v in active_masks.items() if v.get("expires_at", float("inf")) < now]
    for k in expired:
        booking_id = active_masks[k].get("booking_id")
        proxy_pool.append(k)
        del active_masks[k]
        bookings.pop(booking_id, None)
        app.logger.info("Expired mask for booking %s, returned %s to pool", booking_id, k)
```

**`add_to_pool()`** -- Add To Pool.

```python
def add_to_pool():
    data = request.get_json() or {}
    numbers = data.get("numbers", [])
    if not numbers:
        return jsonify({"error": "numbers array required"}), 400
    proxy_pool.extend(numbers)
    return jsonify({"status": "added", "pool_size": len(proxy_pool)})
```

**`create_booking()`** -- Create Booking.

```python
def create_booking():
    ttl_cleanup_masks()
    data = request.get_json() or {}
    party_a = data.get("party_a")
    party_b = data.get("party_b")
    booking_id = data.get("booking_id", f"book-{int(time.time())}")
    hours = data.get("duration_hours", 24)
    if not party_a or not party_b:
        return jsonify({"error": "party_a and party_b required"}), 400
    if not proxy_pool:
        return jsonify({"error": "No proxy numbers available"}), 503
    proxy = proxy_pool.pop(0)
```

**`expire_booking()`** -- Expire Booking.

```python
def expire_booking(booking_id):
    mask = bookings.pop(booking_id, None)
    if not mask:
        return jsonify({"error": "Not found"}), 404
    proxy = mask["proxy"]
    active_masks.pop(proxy, None)
    proxy_pool.append(proxy)
    return jsonify({"status": "expired", "booking_id": booking_id, "proxy_returned": proxy})
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
    ttl_cleanup_masks()

```

**`list_bookings()`** -- List Bookings.

```python
def list_bookings():
    ttl_cleanup_masks()
    return jsonify({"bookings": list(bookings.values()), "pool_available": len(proxy_pool)})
```


### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/pool` | Pool |
| `POST` | `/bookings` | Bookings |
| `DELETE` | `/bookings/<booking_id>` | <Booking Id> |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/bookings` | Bookings |
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
{"status": "ok", "service": "edge-number-masking"}
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
