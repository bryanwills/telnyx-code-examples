# API Reference

Base URL while running locally:

```text
http://localhost:5000
```

## `POST /webhooks/voice`

Receives Telnyx Call Control webhooks. On inbound calls, the app answers the call and starts the configured AI Assistant with `ai_assistant_start`.

Configure this endpoint as your Call Control Application webhook:

```text
https://your-public-url.example.com/webhooks/voice
```

## `POST /tools/create_refill_request`

Assistant tool endpoint that stores a minimal prescription refill request.

```bash
curl -X POST http://localhost:5000/tools/create_refill_request \
  -H "Content-Type: application/json" \
  -H "X-Refill-Tool-Secret: $TOOL_SECRET" \
  -d '{
    "caller_phone": "+18005550199",
    "medication_name": "lisinopril",
    "dosage": "10 mg",
    "pharmacy_name": "main street pharmacy",
    "days_remaining": 5,
    "callback_requested": false,
    "minimum_summary": "caller requests lisinopril refill and has five days remaining"
  }'
```

## `POST /tools/flag_manual_review`

Assistant tool endpoint that marks a refill request for manual pharmacy review.

```bash
curl -X POST http://localhost:5000/tools/flag_manual_review \
  -H "Content-Type: application/json" \
  -H "X-Refill-Tool-Secret: $TOOL_SECRET" \
  -d '{
    "request_id": "refill-9f1c2a3b4d",
    "review_priority": "same_day",
    "review_reason": "caller has less than two days of medication remaining"
  }'
```

## `POST /tools/queue_callback`

Assistant tool endpoint that queues a pharmacy team callback.

```bash
curl -X POST http://localhost:5000/tools/queue_callback \
  -H "Content-Type: application/json" \
  -H "X-Refill-Tool-Secret: $TOOL_SECRET" \
  -d '{
    "request_id": "refill-9f1c2a3b4d",
    "caller_phone": "+18005550199",
    "callback_window": "next business day"
  }'
```

## `POST /dynamic-variables`

Returns assistant context for clinic name, callback window, and emergency wording.

```bash
curl -X POST http://localhost:5000/dynamic-variables \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response:

```json
{
  "dynamic_variables": {
    "clinic_name": "valley health clinic",
    "callback_window": "next business day",
    "emergency_instruction": "if this may be a medical emergency, hang up and call 9-1-1 immediately"
  }
}
```

## `GET /refills/requests`

Lists recent refill requests.

```bash
curl http://localhost:5000/refills/requests
```

## `GET /health`

Checks service status.

```bash
curl http://localhost:5000/health
```
