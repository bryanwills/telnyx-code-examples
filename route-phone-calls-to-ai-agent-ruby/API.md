# API Reference

Typed endpoint reference for this example. The app exposes two HTTP routes and
calls two Telnyx Call Control commands via the Telnyx Ruby SDK (v5.x).

## App routes (served by `app.rb`)

### `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. The Ed25519 signature is verified
over the raw request body **before** the body is parsed or trusted.

#### Request headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Telnyx-Signature-Ed25519` | `string` (base64) | yes | Signature of `"<timestamp>|<raw body>"` |
| `Telnyx-Timestamp` | `string` (unix seconds) | yes | Rejected if `|now - timestamp| > 300s` |
| `Content-Type` | `string` | yes | `application/json` |

#### Request body (Telnyx Call Control event)

```json
{
  "data": {
    "event_type": "call.initiated",
    "id": "0ccc7b54-4df3-4bca-a65a-3da1ecc777f0",
    "occurred_at": "2026-06-19T14:30:00.000Z",
    "record_type": "event",
    "payload": {
      "call_control_id": "v3:uMi2qMWHT-mLFGkEm4t9tA",
      "call_leg_id": "428c31b6-7af4-4bcb-b7f5-5013ef9657c1",
      "call_session_id": "428c31b6-abcd-1234-5678-5013ef9657c1",
      "connection_id": "1494404757140276705",
      "from": "+12125551234",
      "to": "+13105559876",
      "direction": "incoming",
      "state": "parked"
    }
  }
}
```

Fields the app reads (all under `data`):

| Field | Type | Description |
|-------|------|-------------|
| `data.event_type` | `string` | One of `call.initiated`, `call.answered`, `call.hangup` (others ignored) |
| `data.payload.call_control_id` | `string` | Identifies the call leg for follow-up commands |
| `data.payload.direction` | `string` | `incoming` / `outgoing`; only `incoming` calls are auto-answered |
| `data.payload.hangup_cause` | `string` | Present on `call.hangup`; logged |

#### Responses

| Status | Body | When |
|--------|------|------|
| `200` | `{"status":"ok"}` | Event accepted (always returned once verified + parsed) |
| `400` | `{"error":"invalid JSON"}` | Body is not valid JSON |
| `401` | `{"error":"invalid signature"}` | Missing/invalid signature or stale timestamp |

### `GET /health`

| Status | Body |
|--------|------|
| `200` | `{"status":"ok"}` |

## Telnyx SDK calls

Client is constructed once: `Telnyx::Client.new(api_key: ENV["TELNYX_API_KEY"])`.

### Answer a call

```ruby
client.calls.actions.answer(call_control_id)
```

- **HTTP:** `POST /v2/calls/{call_control_id}/actions/answer`
- **Args:** `call_control_id` (`String`, positional, required)
- **Returns:** a response model whose `.data.result` is `"ok"` on success.

### Start the AI assistant on the call

```ruby
client.calls.actions.start_ai_assistant(
  call_control_id,
  assistant: { id: ENV["TELNYX_ASSISTANT_ID"] }
)
```

- **HTTP:** `POST /v2/calls/{call_control_id}/actions/start_ai_assistant`
- **Args:**
  - `call_control_id` (`String`, positional, required)
  - `assistant:` (`Hash`, keyword) — `{ id: "<assistant_id>" }`; optional keys include `greeting:`, `voice:` (confirm field-level constraints against developers.telnyx.com)
- **Returns:** a response model whose `.data.result` is `"ok"` on success.

## Errors

SDK errors are namespaced under `Telnyx::Errors::*` in v5.x and are caught in the
webhook handler so exception details never reach the HTTP response:

| Exception | Meaning |
|-----------|---------|
| `Telnyx::Errors::AuthenticationError` | Invalid `TELNYX_API_KEY` |
| `Telnyx::Errors::RateLimitError` | HTTP 429 from Telnyx |
| `Telnyx::Errors::APIStatusError` | Non-2xx HTTP response; `e.status` is the integer status code |
| `Telnyx::Errors::APIConnectionError` | Network failure reaching Telnyx |
| `Telnyx::Errors::APIError` | Base class; catch-all for other SDK errors |
