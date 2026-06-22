# API Reference

This service exposes two HTTP endpoints: one to place an outbound call through Telnyx Call Control, and one to receive signature-verified call webhooks.

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
| `to` | `string` | **yes** | Destination phone number in E.164 format (must start with `+`) or a `sip:` URI |

The originating number (`from`) and the Call Control Application (`connection_id`) are read from the server environment (`TELNYX_PHONE_NUMBER`, `TELNYX_CONNECTION_ID`) and are not part of the request body.

### Response `200`

```json
{
  "call_control_id": "v3:abc123def456...",
  "call_session_id": "00000000-0000-0000-0000-000000000000",
  "call_leg_id": "00000000-0000-0000-0000-000000000000",
  "is_alive": true,
  "from": "+15551234567",
  "to": "+12125551234"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `call_control_id` | `string` | Telnyx identifier for the call, used in subsequent call control commands |
| `call_session_id` | `string` (GUID) | Groups all legs of a single call session |
| `call_leg_id` | `string` (GUID) | Identifier for this specific call leg |
| `is_alive` | `boolean` | Whether the call is currently active |
| `from` | `string` | Originating Telnyx number (E.164) |
| `to` | `string` | Destination number that was dialed (E.164) |

### Try it

```bash
curl -X POST http://localhost:5000/calls/dial \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234"}'
```

---

## `POST /webhooks/calls`

Receive Telnyx call lifecycle events (`call.initiated`, `call.answered`, `call.hangup`, ...).

### Request

Sent by Telnyx. The handler reads the **raw** request body and these headers:

| Header | Description |
|--------|-------------|
| `telnyx-signature-ed25519` | Base64 Ed25519 signature of `"{timestamp}|{raw body}"` |
| `telnyx-timestamp` | Unix timestamp included in the signed message (300s tolerance) |

The body is verified with `Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(rawBody, signature, timestamp, publicKey)`. Event fields are read from `data.payload`.

### Responses

| Status | Meaning | When it happens |
|--------|---------|-----------------|
| `200` | Acknowledged | Signature verified and event processed |
| `401` | Unauthorized | Signature missing/invalid or timestamp outside tolerance (`TelnyxException`) |
| `500` | Server error | `TELNYX_PUBLIC_KEY` not configured |

---

## Error Handling

All `/calls/dial` responses are JSON. On validation error the body has the shape `{"error": "..."}`. Upstream Telnyx failures surface as `TelnyxException`, which is logged server-side and returned as a generic status — exception detail is never leaked to the client.

| Status | Meaning | When it happens |
|--------|---------|-----------------|
| `200` | Success | Call was initiated |
| `400` | Bad request | Missing `to`, non-E.164 number, or a missing required environment variable (`TELNYX_PHONE_NUMBER` / `TELNYX_CONNECTION_ID`) |
| `502` | Upstream error | The Telnyx API rejected the request (`TelnyxException`) — e.g. bad API key, unknown `connection_id`, unverified number |
| `500` | Internal server error | Unhandled error |

---

## Telnyx API Endpoints Called

The server calls the Telnyx API through the official .NET SDK (`Telnyx.net`).

| SDK call | HTTP | Path | Purpose |
|----------|------|------|---------|
| `new CallControlService().DialAsync(new CallControlDialOptions { To, From, ConnectionId })` | `POST` | `/v2/calls` | Initiate an outbound call. `ConnectionId` is **required** and links the call to your Call Control Application; `CallControlId` is **returned** on the `CallDialResponse` — do not pass it as input. |
| `Webhook.ConstructEvent(rawBody, signature, timestamp, publicKey)` | — | — | Verify the Ed25519 signature of an inbound webhook and return `TelnyxWebhook<object>`. |

See the [Dial API reference](https://developers.telnyx.com/api-reference/call-commands/dial).
