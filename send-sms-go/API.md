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
  "message_id": "msg-f5d7a7e0-1234-5678",
  "status": "queued",
  "from": "+15551234567",
  "to": "+12125559999"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | `string` | Telnyx message ID (`response.Data.ID`) |
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

The handler calls one Telnyx endpoint through the Go SDK:

| SDK call | HTTP | Telnyx endpoint |
|----------|------|-----------------|
| `client.Messaging.CreateMessage(params)` | `POST` | `/v2/messages` |

`CreateMessageParams` is populated with `From` (from `TELNYX_PHONE_NUMBER`), `To`, and `Text`.

---

## Error Handling

All responses are JSON. On error the body is `{"error": "..."}`. Telnyx SDK error types are mapped to HTTP status codes:

| Status | Trigger | Body |
|--------|---------|------|
| `200` | Message accepted by Telnyx | success object above |
| `400` | Missing `to`/`message`, or non-E.164 number, or other validation error | `{"error": "Missing required fields: 'to' and 'message'"}` / `{"error": "phone number must be in E.164 format (e.g., +15551234567)"}` |
| `401` | `*telnyx.AuthenticationError` — invalid API key | `{"error": "Invalid API key"}` |
| `429` | `*telnyx.RateLimitError` | `{"error": "Rate limit exceeded. Please slow down."}` |
| `503` | `*telnyx.APIConnectionError` — network error reaching Telnyx | `{"error": "Network error connecting to Telnyx"}` |
| varies | `*telnyx.APIStatusError` — other API error | `{"error": "<message>", "status_code": <code>}` |
