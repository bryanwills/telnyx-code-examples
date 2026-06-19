## `POST /sms/send`

Send a single SMS via the Telnyx Messaging API. Handled by `SmsController#send_sms` in `app.rb`.

### Request

```json
{
  "to": "+12125559999",
  "message": "Hello from the API"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number in E.164 format (must start with `+`) |
| `message` | `string` | **yes** | Message text to send |

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
| `message_id` | `string` | Telnyx message ID (`response.data.id`) |
| `status` | `string` | Delivery status of the first recipient, or `"unknown"` if absent |
| `from` | `string` | Sending number, from `TELNYX_PHONE_NUMBER` |
| `to` | `string` | Destination number echoed from the request |

**Try it:**

```bash
curl -X POST http://localhost:3000/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125559999", "message": "Hello from the API"}'
```

---

## Telnyx API Endpoints Called

| Telnyx Endpoint | SDK Call | Purpose |
|-----------------|----------|---------|
| `POST /v2/messages` | `client.messages.create(from_:, to:, text:)` | Send an outbound SMS |

The client is created per request with `Telnyx::Client.new(api_key: ENV["TELNYX_API_KEY"])`.

---

## Error Handling

All responses are JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning | Trigger |
|--------|---------|---------|
| `200` | Success | Message accepted by Telnyx |
| `400` | Bad request | Missing `to`/`message`, or `to` not in E.164 format |
| `401` | Unauthorized | `Telnyx::AuthenticationError` — invalid API key |
| `429` | Too many requests | `Telnyx::RateLimitError` — rate limit exceeded |
| `500` | Server error | `TELNYX_PHONE_NUMBER` not set |
| `503` | Service unavailable | `Telnyx::APIConnectionError` — network error reaching Telnyx |
| (passthrough) | Telnyx API error | `Telnyx::APIStatusError` — response carries Telnyx's `status_code` plus a `status_code` field |
