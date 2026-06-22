# API Reference

Two HTTP routes are defined in `app.rb`: one to place a call, one to receive
Telnyx call lifecycle webhooks.

## `POST /calls/dial`

Place an outbound Call Control call via the Telnyx Voice API.

### Request

```json
{
  "to": "+12125559999"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number in E.164 format (must start with `+`) |

The `from` number and the Call Control Application (`connection_id`) come from
the `TELNYX_PHONE_NUMBER` and `TELNYX_CONNECTION_ID` environment variables, not
the request body.

### Response `200`

```json
{
  "call_control_id": "v3:uMi2qMWHT-mLFGkEm4t9tA",
  "call_leg_id": "428c31b6-7af4-4bcb-b68e-5013ef9657c1",
  "call_session_id": "428c31b6-abc4-4cba-1234-5013ef9657c1",
  "is_alive": true,
  "from": "+15551234567",
  "to": "+12125559999"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `call_control_id` | `string` | Identifier used to issue follow-up Call Control commands (`response.data.call_control_id`) |
| `call_leg_id` | `string` | Unique ID of this call leg (`response.data.call_leg_id`) |
| `call_session_id` | `string` | ID grouping legs of the same session (`response.data.call_session_id`) |
| `is_alive` | `boolean` | Whether the call leg is currently active (`response.data.is_alive`) |
| `from` | `string` | Sending number, from `TELNYX_PHONE_NUMBER` |
| `to` | `string` | Destination number echoed from the request |

**Try it:**

```bash
curl -X POST http://localhost:4567/calls/dial \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125559999"}'
```

---

## `POST /webhooks/voice`

Receives call lifecycle events from Telnyx and verifies the Ed25519 signature
before trusting the body.

### Request headers

| Header | Description |
|--------|-------------|
| `telnyx-signature-ed25519` | Base64 Ed25519 signature over `"<timestamp>|<raw-body>"` |
| `telnyx-timestamp` | Unix seconds; rejected if older than 300s (replay protection) |

### Request body (example)

```json
{
  "data": {
    "event_type": "call.answered",
    "payload": {
      "call_control_id": "v3:uMi2qMWHT-mLFGkEm4t9tA",
      "direction": "outgoing",
      "from": "+15551234567",
      "to": "+12125559999"
    }
  }
}
```

Handled `event_type` values: `call.initiated`, `call.answered`, `call.hangup`.
All event fields are read from `data.payload`.

### Responses

```json
{ "received": true }
```

| Status | Meaning | Trigger |
|--------|---------|---------|
| `200` | Accepted | Signature valid; event processed |
| `400` | Bad request | Body is not valid JSON |
| `401` | Unauthorized | Missing/invalid signature, or stale timestamp |

---

## Telnyx API Endpoints Called

| Telnyx Endpoint | SDK Call | Purpose |
|-----------------|----------|---------|
| `POST /v2/calls` | `client.calls.dial(connection_id:, from:, to:, webhook_url:)` | Place an outbound call |

The client is created once per process with
`Telnyx::Client.new(api_key: ENV["TELNYX_API_KEY"])`.

---

## Error Handling

All responses are JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning | Trigger |
|--------|---------|---------|
| `200` | Success | Call accepted by Telnyx |
| `400` | Bad request | Missing `to`, `to` not in E.164 format, or invalid JSON |
| `401` | Unauthorized | `Telnyx::Errors::AuthenticationError` — invalid API key |
| `429` | Too many requests | `Telnyx::Errors::RateLimitError` — rate limit exceeded |
| `500` | Server error | `TELNYX_CONNECTION_ID`/`TELNYX_PHONE_NUMBER` not set, or unexpected error |
| `502` | Bad gateway | `Telnyx::Errors::APIStatusError` with a non-HTTP upstream status |
| `503` | Service unavailable | `Telnyx::Errors::APIConnectionError` — network error reaching Telnyx |
| (passthrough) | Telnyx API error | `Telnyx::Errors::APIStatusError` — echoes Telnyx's HTTP status |

Internal exception messages are logged via `logger.error` and never returned in
HTTP responses.
