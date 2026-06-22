# API Reference

Typed endpoint reference for the inbound SMS webhook receiver.

## `POST /webhooks/sms`

Receive an inbound SMS webhook event (`message.received`) from Telnyx. The handler reads the raw request body, verifies the Telnyx Ed25519 signature over `"<telnyx-timestamp>|<raw body>"` via `client.webhooks().unwrap(...)`, reads the message from `data.payload`, and acknowledges with `200 OK`. Telnyx requires a 2xx response within 5 seconds or it retries delivery.

### Request headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `telnyx-signature-ed25519` | `string` | **yes** | Base64 64-byte Ed25519 signature. Missing → `401`. |
| `telnyx-timestamp` | `string` | **yes** | Unix seconds. Must be within a 300s window; otherwise the signature is rejected. Missing → `401`. |
| `Content-Type` | `string` | no | Typically `application/json`. The signature is verified over the raw bytes regardless. |

### Request body

Sent by Telnyx. Message fields are nested under `data.payload`.

```json
{
  "data": {
    "event_type": "message.received",
    "payload": {
      "id": "msg-f5d7a7e0-1234-5678",
      "from": { "phone_number": "+12125551234" },
      "to": [{ "phone_number": "+13125559876" }],
      "text": "Hello from a real phone",
      "received_at": "2026-06-18T12:00:00Z",
      "direction": "inbound"
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | `object` | **yes** | Webhook envelope. |
| `data.payload` | `object` | **yes** | Inbound message payload. Read via `event.inboundMessage().data().payload()`. |
| `data.payload.id` | `string` | no | Telnyx message ID. `null` if absent. |
| `data.payload.from.phone_number` | `string` | no | Sender number (E.164). |
| `data.payload.to[0].phone_number` | `string` | no | Recipient number (E.164). |
| `data.payload.text` | `string` | no | Message body. Defaults to `""`. |

### Response `200`

```json
{
  "status": "received",
  "message_id": "msg-f5d7a7e0-1234-5678"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | `"received"` for a verified inbound SMS; `"ignored"` for verified non-SMS events or events without a payload. |
| `message_id` | `string` \| `null` | The processed message ID (`null` if not provided). Only present on `"received"`. |

### Response `401`

```json
{ "error": "invalid signature" }
```

Returned when signature headers are missing (`{"error":"missing signature headers"}`), or when `unwrap()` fails verification (bad signature, stale timestamp, or missing/incorrect `TELNYX_PUBLIC_KEY`).

### Response `405`

```json
{ "error": "method not allowed" }
```

Returned for non-`POST` methods.

### Response `500`

```json
{ "error": "internal server error" }
```

Generic message only — exception details are logged via `java.util.logging`, never returned to the caller.

---

## `GET /health`

Liveness probe.

### Request

No parameters.

### Response `200`

```json
{ "status": "ok" }
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"`. |

---

## Telnyx SDK calls used

This service is a webhook **receiver** — it makes no outbound Telnyx REST calls. It uses one SDK method:

| SDK call | Purpose |
|----------|---------|
| `TelnyxOkHttpClient.fromEnv()` | Build the shared client from `TELNYX_API_KEY` and `TELNYX_PUBLIC_KEY`. |
| `client.webhooks().unwrap(UnwrapWebhookParams)` | Verify the Ed25519 signature and parse the event. Throws on a bad/stale signature or a parse error. |
| `event.inboundMessage().data().payload()` | Read the `InboundMessagePayload` (id / from / to / text) from `data.payload`. |

See the [Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message) and the [webhook signing reference](https://developers.telnyx.com/api-reference/webhooks/verify-webhook-signatures).
