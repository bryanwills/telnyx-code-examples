# API Reference

## `POST /sms/send`

Send a single SMS message via Telnyx.

### Request

`Content-Type: application/json`

```json
{
  "to": "+12125559999",
  "message": "Hello from the API"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number in E.164 format (must start with `+`) |
| `message` | `string` | **yes** | Message body to send (mapped to the Telnyx `Text` field) |

### Response `200`

```json
{
  "message_id": "40017f3c-bba0-4f3f-8b2c-1a8d0c1f9c11",
  "from": "+15551234567",
  "to": "+12125559999"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | `string` (GUID) | Telnyx message ID (`MessagingSenderId.Id`, from the response `data.id`) |
| `from` | `string` | Sending number (`TELNYX_PHONE_NUMBER`) |
| `to` | `string` | Destination number as provided |

**Try it:**

```bash
curl -X POST http://localhost:5000/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125559999", "message": "Hello from the API"}'
```

---

## `POST /webhooks/sms`

Receives inbound message webhooks from Telnyx (e.g. `message.received`, `message.finalized`).

### Request

Telnyx sends a JSON body plus signature headers:

| Header | Description |
|--------|-------------|
| `telnyx-signature-ed25519` | Base64 Ed25519 signature over `"{telnyx-timestamp}|{raw body}"` |
| `telnyx-timestamp` | Unix timestamp used in the signed message; enforced within a 300s tolerance |

The handler reads the **raw** request body before any parsing and calls
`Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(rawBody, signature, timestamp, TELNYX_PUBLIC_KEY)`,
which returns a `TelnyxWebhook<object>`. Event fields are read from `evt.Data`
(`EventType`, `Id`, `OccurredAt`, `RecordType`) and the inbound content from
`evt.Data.Payload` (the `data.payload` object).

### Responses

| Status | Meaning | Trigger |
|--------|---------|---------|
| `200` | Verified | Signature valid and timestamp within tolerance |
| `401` | Unauthorized | Missing/invalid signature or stale timestamp (`TelnyxException`) |
| `500` | Server error | `TELNYX_PUBLIC_KEY` not configured |

---

## Error Handling

All responses are JSON. On error the body is `{"error": "..."}`. Exception details are logged
server-side via `app.Logger` and never returned in the HTTP response.

| Status | Meaning | Trigger |
|--------|---------|---------|
| `200` | Success | Message accepted by Telnyx |
| `400` | Bad request | Missing `to`/`message`, non-E.164 number, or unset `TELNYX_PHONE_NUMBER` |
| `401` | Unauthorized | Invalid webhook signature / stale timestamp |
| `500` | Server error | Unexpected error, or `TELNYX_PUBLIC_KEY` missing for webhooks |
| `502` | Bad gateway | Telnyx API call failed (`Telnyx.TelnyxException`) |

The Telnyx.net SDK raises a single exception type, `Telnyx.TelnyxException`, for all API failures
(there are no separate `AuthenticationError` / `RateLimitError` / `APIStatusError` types).

---

## Telnyx API Endpoints Called

| Method | Path | SDK call | Purpose |
|--------|------|----------|---------|
| `POST` | `/v2/messages` | `new MessagingSenderIdService().CreateAsync(new NewMessagingSenderId { From, To, Text })` | Send the SMS |

- [Send a Message — API reference](https://developers.telnyx.com/api-reference/messages/send-a-message)
