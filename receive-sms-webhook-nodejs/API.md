## `POST /webhooks/sms`

Receive an inbound SMS webhook event from Telnyx. Validates the payload structure, extracts the message, stores it in memory, and acknowledges with `200 OK`. Telnyx requires a 2xx response within 5 seconds or it will retry delivery.

### Request

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
| `data.payload` | `object` | **yes** | Message payload. Rejected with `400` if absent. |
| `data.payload.id` | `string` | no | Telnyx message ID. Defaults to `null` if missing. |
| `data.payload.from.phone_number` | `string` | **yes** | Sender number (E.164). Rejected with `400` if missing. |
| `data.payload.to[0].phone_number` | `string` | **yes** | Recipient number (E.164). Rejected with `400` if missing. |
| `data.payload.text` | `string` | no | Message body. Defaults to `""` if missing. |
| `data.payload.received_at` | `string` | no | ISO 8601 timestamp. Defaults to server time if missing. |
| `data.payload.direction` | `string` | no | Message direction. Defaults to `"inbound"`. |

### Response `200`

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
| `status` | `string` | Always `"received"`. |

### Try it

```bash
curl -X POST http://localhost:5000/webhooks/sms \
  -H "Content-Type: application/json" \
  -d '{"data":{"event_type":"message.received","payload":{"id":"msg-1","from":{"phone_number":"+12125551234"},"to":[{"phone_number":"+13125559876"}],"text":"Hi"}}}'
```

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

### Try it

```bash
curl http://localhost:5000/messages
```

---

## `GET /health`

Liveness check.

### Request

No parameters.

### Response `200`

```json
{
  "status": "ok",
  "timestamp": "2026-06-18T12:00:00.000Z"
}
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

None. This service is a webhook **receiver**. The Telnyx SDK client is initialized with `TELNYX_API_KEY`, but the request flow is inbound: Telnyx delivers `message.received` events to `POST /webhooks/sms`. See the [Receive a Message guide](https://developers.telnyx.com/docs/messaging/messages/receive-message).

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success — webhook accepted or read succeeded |
| `400` | Bad request — missing `data`, missing `data.payload`, or missing sender/recipient number |
| `500` | Server error — unhandled exception (returns `error` and `message`) |
