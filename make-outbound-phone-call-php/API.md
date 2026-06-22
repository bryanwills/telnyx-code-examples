# API Reference

This service exposes two HTTP endpoints: one to place an outbound call through
Telnyx Call Control, and one to receive signature-verified call webhooks.

## `POST /calls/dial`

Initiate an outbound call from your Telnyx number to a destination number.

### Request

```json
{
  "to": "+12125551234"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number in E.164 format (must start with `+`) |

The originating number (`from`) and the Call Control Application (`connectionID`)
are read from the server environment (`TELNYX_PHONE_NUMBER`, `TELNYX_CONNECTION_ID`)
and are not part of the request body.

### Response `200`

```json
{
  "call_control_id": "v3:abc123def456...",
  "call_leg_id": "0ccc7b54-...",
  "call_session_id": "0ccc7b54-...",
  "is_alive": true,
  "from": "+15551234567",
  "to": "+12125551234"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `call_control_id` | `string` | Telnyx identifier for the call, used in subsequent call control commands |
| `call_leg_id` | `string` | Identifier of the call leg |
| `call_session_id` | `string` | Identifier of the call session |
| `is_alive` | `boolean` | Whether the call is currently active |
| `from` | `string` | Originating Telnyx number (E.164) |
| `to` | `string` | Destination number that was dialed (E.164) |

### Try it

```bash
curl -X POST http://localhost:8080/calls/dial \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234"}'
```

---

## `POST /webhooks/calls`

Receives Telnyx call control webhooks. The raw body and headers are passed to
`$client->webhooks->unwrap()`, which verifies the Ed25519 signature (using
`TELNYX_PUBLIC_KEY`) and parses the event. Event data is read from `data.payload`.

### Headers (set by Telnyx)

| Header | Description |
|--------|-------------|
| `Telnyx-Signature-Ed25519` | Base64 Ed25519 signature over `"{timestamp}|{body}"` |
| `Telnyx-Timestamp` | Unix timestamp; a 300s tolerance protects against replay |

### Response

| Status | Body | When |
|--------|------|------|
| `200` | `{"status": "ok", "event_type": "call.answered"}` | Signature verified |
| `401` | `{"error": "Invalid signature"}` | Signature missing/invalid (`WebhookException`) |
| `400` | `{"error": "Bad request"}` | Body could not be processed |

---

## Error Handling

All responses are JSON with the shape `{"error": "..."}` on failure (the upstream
status case also includes a `status_code` field). Internal exception details are
logged via `error_log()` and never returned to the client.

| Status | Meaning | When it happens |
|--------|---------|-----------------|
| `200` | Success | Call was initiated / webhook verified |
| `400` | Bad request | Missing `to`, non-E.164 number, or a missing required environment variable |
| `401` | Invalid API key / signature | `AuthenticationException` (dial) or `WebhookException` (webhook) |
| `429` | Rate limit exceeded | `RateLimitException` |
| `503` | Network error connecting to Telnyx | `APIConnectionException` |
| _passthrough_ | Telnyx API status error | `APIStatusException` — responds with the upstream `status` |
| `500` | Internal server error | Unhandled error |

---

## Telnyx API Endpoints Called

The server calls the Telnyx API through the PHP SDK.

| SDK call | HTTP | Path | Purpose |
|----------|------|------|---------|
| `$client->calls->dial(connectionID, from, to)` | `POST` | `/v2/calls` | Initiate an outbound call. `connectionID` is **required** and links the call to your Call Control Application; `call_control_id` is **returned** in the response — do not pass it as input. |
| `$client->webhooks->unwrap($body, $headers)` | — | — | Verify the Ed25519 signature and parse an inbound webhook event. |

See the [Dial API reference](https://developers.telnyx.com/api-reference/call-commands/dial).
