# API Reference

## `POST /sms/send`

Send a single SMS message via the Telnyx Messaging API.

### Request

```json
{
  "to": "+12125559999",
  "message": "Hello from the API"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number (E.164, must start with `+`) |
| `message` | `string` | **yes** | Message content to send |

### Response `200`

```json
{
  "message_id": "40385f64-5717-4562-b3fc-2c963f66afa6",
  "status": "queued",
  "from": "+15551234567",
  "to": "+12125559999"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | `string` | Telnyx message ID (`response.data().flatMap(d -> d.id())`) |
| `status` | `string` | Delivery status of the first recipient, or `unknown` if unavailable |
| `from` | `string` | The `TELNYX_PHONE_NUMBER` the message was sent from |
| `to` | `string` | The destination number echoed back |

**Try it:**

```bash
curl -X POST http://localhost:5000/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125559999", "message": "Hello from the API"}'
```

---

## Telnyx Endpoints Called

The handler calls one Telnyx endpoint through the Java SDK:

| SDK call | HTTP | Telnyx endpoint |
|----------|------|-----------------|
| `client.messages().send(params)` | `POST` | `/v2/messages` |

`MessageSendParams` is built with `from` (from `TELNYX_PHONE_NUMBER`), `to`, and `text`:

```java
MessageSendParams params = MessageSendParams.builder()
        .from(fromNumber)
        .to(to)
        .text(message)
        .build();
MessageSendResponse response = client.messages().send(params);
```

`MessageSendResponse.data()` returns `Optional<OutboundMessagePayload>`. The message id
is read via `response.data().flatMap(d -> d.id())`, and the first recipient status via
`response.data().flatMap(d -> d.to()).flatMap(list -> list.stream().findFirst()).flatMap(t -> t.status())`.

---

## Error Handling

All responses are JSON. On error the body is `{"error": "..."}`. Provider error
details are logged server-side (`java.util.logging`) and never returned to the caller.

| Status | Trigger | Body |
|--------|---------|------|
| `200` | Message accepted by Telnyx | success object above |
| `400` | Missing `to`/`message`, invalid JSON, or non-E.164 number | `{"error": "Missing required fields: 'to' and 'message'"}` / `{"error": "Phone number must be in E.164 format (e.g., +15551234567)"}` |
| `401` | `TelnyxServiceException` with `statusCode() == 401` — invalid API key | `{"error": "Invalid API key"}` |
| `405` | Non-`POST` request to `/sms/send` | `{"error": "Method not allowed"}` |
| `429` | `TelnyxServiceException` with `statusCode() == 429` — rate limited | `{"error": "Rate limit exceeded. Please slow down."}` |
| `502` | Other `TelnyxServiceException` (API rejected the request) | `{"error": "Failed to send message"}` |
| `503` | Unexpected/transport error reaching Telnyx | `{"error": "Network error connecting to Telnyx"}` |
