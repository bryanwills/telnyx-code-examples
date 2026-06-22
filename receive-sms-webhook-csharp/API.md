# API Reference

This service is a webhook **receiver**. Telnyx delivers signed `message.received`
events to `POST /webhooks/sms`. The signature is verified before the body is trusted.

## `POST /webhooks/sms`

Receive an inbound SMS webhook event from Telnyx. The handler:

1. Reads the **raw** request body (no model binding/parsing first).
2. Verifies the Ed25519 signature over `"<telnyx-timestamp>|<raw body>"` using
   `Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent`.
3. Reads message fields from `data.payload`.
4. Acknowledges with `200 OK` (Telnyx retries unless it gets a 2xx within 5 seconds).

### Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `telnyx-signature-ed25519` | `string` | **yes** | Base64 Ed25519 signature. Missing → `401`. |
| `telnyx-timestamp` | `string` | **yes** | Unix seconds. Part of the signed message; stale timestamps → `401`. |
| `Content-Type` | `string` | no | Telnyx sends `application/json`. |

### Request Body

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
| `data.event_type` | `string` | **yes** | Only `message.received` is processed; others return `200 {"status":"ignored"}`. |
| `data.payload` | `object` | **yes** | Message payload. Missing → `400`. |
| `data.payload.id` | `string` | no | Telnyx message ID. Defaults to `null`. |
| `data.payload.from.phone_number` | `string` | **yes** | Sender number (E.164). Missing → `400`. |
| `data.payload.to[0].phone_number` | `string` | **yes** | Recipient number (E.164). Missing → `400`. |
| `data.payload.text` | `string` | no | Message body. Defaults to `""`. |
| `data.payload.received_at` | `string` | no | ISO 8601 timestamp. Defaults to server time. |
| `data.payload.direction` | `string` | no | Message direction. Defaults to `"inbound"`. |

### Response `200` (verified `message.received`)

```json
{
  "success": true,
  "message_id": "msg-f5d7a7e0-1234-5678",
  "status": "received"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | Always `true` on an accepted message. |
| `message_id` | `string` \| `null` | Processed message ID (`null` if not provided). |
| `status` | `string` | Always `"received"`. |

### Response `200` (other verified event)

```json
{ "status": "ignored" }
```

### Other Responses

| Status | Meaning |
|--------|---------|
| `401 Unauthorized` | Missing signature/timestamp header, bad signature, or stale timestamp. |
| `400 Bad Request` | Verified body has no `data.payload`, missing sender/recipient number, or is not valid JSON. |
| `503 Service Unavailable` | `TELNYX_PUBLIC_KEY` is not configured — the server cannot verify and fails closed. |

Error responses are generic JSON (`{"error": "..."}`); exception detail is logged
server-side only, never returned to the caller.

---

## `GET /messages`

Return all messages received since the server started. In-memory — remove in production.

### Response `200`

```json
{
  "count": 1,
  "messages": [
    {
      "messageId": "msg-f5d7a7e0-1234-5678",
      "from": "+12125551234",
      "to": "+13125559876",
      "text": "Hello from a real phone",
      "receivedAt": "2026-06-18T12:00:00Z",
      "direction": "inbound"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `count` | `number` | Number of stored messages. |
| `messages` | `array` | List of processed message objects. |

### Try it

```bash
curl http://localhost:5000/messages
```

---

## `GET /health`

Liveness check.

### Response `200`

```json
{ "status": "ok", "timestamp": "2026-06-18T12:00:00.0000000Z" }
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"`. |
| `timestamp` | `string` | Current server time (ISO 8601). |

### Try it

```bash
curl http://localhost:5000/health
```

---

## Telnyx API Endpoints Called

None. This service receives webhooks; it does not call the Telnyx REST API. See the
[Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message).
