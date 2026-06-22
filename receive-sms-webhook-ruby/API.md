# API Reference

Typed endpoint reference for the Sinatra inbound-SMS webhook receiver.

## `POST /webhooks/sms`

Receive an inbound SMS webhook event from Telnyx. The handler:

1. Reads the **raw** request body.
2. Verifies the Telnyx Ed25519 signature over `"<telnyx-timestamp>|<raw-body>"`.
3. Parses the JSON and reads message fields from `data.payload`.
4. Stores the message and acknowledges with `200 OK`.

Telnyx requires a 2xx response within 5 seconds or it retries delivery.

### Request headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `telnyx-signature-ed25519` | `string` (base64) | **yes** | Ed25519 signature of `"<timestamp>\|<raw-body>"`. Rejected with `401` if absent or invalid. |
| `telnyx-timestamp` | `string` (unix seconds) | **yes** | Send time. Rejected with `401` if absent or more than 300s from server time (replay protection). |
| `Content-Type` | `string` | no | Typically `application/json`. The body is read raw regardless. |

### Request body

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
| `data` | `object` | **yes** | Webhook envelope. Request is rejected with `400` if absent. |
| `data.event_type` | `string` | no | Only `message.received` is processed; other types are acknowledged with `200` and ignored. |
| `data.payload` | `object` | **yes** (for `message.received`) | Message payload. Rejected with `400` if absent. |
| `data.payload.id` | `string` | no | Telnyx message ID. `null` if missing. |
| `data.payload.from.phone_number` | `string` | **yes** | Sender number (E.164). Rejected with `400` if missing. |
| `data.payload.to[0].phone_number` | `string` | **yes** | Recipient number (E.164). Rejected with `400` if missing. |
| `data.payload.text` | `string` | no | Message body. Defaults to `""`. |
| `data.payload.received_at` | `string` | no | ISO 8601 timestamp. Defaults to server time. |
| `data.payload.direction` | `string` | no | Message direction. Defaults to `"inbound"`. |

### Response `200` (message.received)

```json
{
  "success": true,
  "message_id": "msg-f5d7a7e0-1234-5678",
  "status": "received"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Always `true` on accepted webhook. |
| `message_id` | `string` \| `null` | The processed message ID (`null` if not provided). |
| `status` | `string` | `"received"`. |

### Response `200` (other event types)

```json
{ "success": true, "status": "ignored" }
```

### Error responses

| Status | Body | Meaning |
|--------|------|---------|
| `401` | `{"error":"invalid signature"}` | Missing/invalid Ed25519 signature, missing timestamp, or timestamp skew > 300s. |
| `400` | `{"error":"Invalid webhook payload"}` | Body is not valid JSON, or has no `data` object. |
| `400` | `{"error":"Invalid webhook payload structure"}` | `message.received` event with no `data.payload`. |
| `400` | `{"error":"Missing sender or recipient phone number in webhook"}` | `from.phone_number` or `to[0].phone_number` absent. |
| `500` | `{"error":"Internal server error"}` | Unhandled exception. Details are logged, never returned. |

---

## `GET /messages`

Return all messages received since the server started. In-memory storage — remove in production.

### Request

No parameters.

### Response `200`

```json
{
  "count": 1,
  "messages": [
    {
      "message_id": "msg-f5d7a7e0-1234-5678",
      "from": "+12125551234",
      "to": "+13125559876",
      "text": "Hello from a real phone",
      "received_at": "2026-06-18T12:00:00Z",
      "direction": "inbound"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `count` | `number` | Number of stored messages. |
| `messages` | `array` | List of processed message objects. |

---

## `GET /health`

Liveness check.

### Request

No parameters.

### Response `200`

```json
{
  "status": "ok",
  "timestamp": "2026-06-18T12:00:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"`. |
| `timestamp` | `string` | Current server time (ISO 8601). |

---

## Telnyx API Endpoints Called

None. This service is a webhook **receiver**. The request flow is inbound: Telnyx
delivers `message.received` events to `POST /webhooks/sms`, signed with Ed25519. See
the [Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message).
