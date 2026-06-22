# API Reference — send-sms-php

## `POST /sms/send`

Send a single SMS via the Telnyx Messaging API. Handled by the front controller in `index.php`.

### Request

Headers: `Content-Type: application/json`

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
| `message_id` | `string` | Telnyx message ID (`$response->data->id`) |
| `status` | `string` | Delivery status of the first recipient, or `"unknown"` if absent |
| `from` | `string` | Sending number, from `TELNYX_PHONE_NUMBER` |
| `to` | `string` | Destination number echoed from the request |

**Try it:**

```bash
curl -X POST http://localhost:8080/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125559999", "message": "Hello from the API"}'
```

---

## Telnyx API Endpoints Called

| Telnyx Endpoint | SDK Call | Purpose |
|-----------------|----------|---------|
| `POST /v2/messages` | `$client->messages->send(to:, from:, text:)` | Send an outbound SMS |

The client is created per request with `new Telnyx\Client(apiKey: getenv('TELNYX_API_KEY'))`.
The SDK uses **named parameters** for `send()` — there is no `messages->create()` method in the 7.x SDK.

The send response is a `Telnyx\Messages\MessageSendResponse`. Useful fields:

| Property | Type | Description |
|----------|------|-------------|
| `$response->data->id` | `string` | Message ID |
| `$response->data->to` | `array` | Recipient objects, each with `phone_number` and `status` |
| `$response->data->from` | `object` | Sending number details |
| `$response->data->text` | `string` | Message body that was sent |
| `$response->data->parts` | `int` | Number of SMS segments |

---

## Error Handling

All responses are JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning | Trigger |
|--------|---------|---------|
| `200` | Success | Message accepted by Telnyx |
| `400` | Bad request | Body not JSON, missing `to`/`message`, or `to` not in E.164 format |
| `401` | Unauthorized | `Telnyx\Core\Exceptions\AuthenticationException` — invalid API key |
| `404` | Not found | Method/path other than `POST /sms/send` |
| `429` | Too many requests | `Telnyx\Core\Exceptions\RateLimitException` — rate limit exceeded |
| `500` | Server error | `TELNYX_PHONE_NUMBER` not set |
| `502` | Bad gateway | Other `Telnyx\Core\Exceptions\APIException` |
| `503` | Service unavailable | `Telnyx\Core\Exceptions\APIConnectionException` — network error reaching Telnyx |
| (passthrough) | Telnyx API error | `Telnyx\Core\Exceptions\APIStatusException` — uses Telnyx's `$e->status` as the HTTP code |

Internal exception messages are written to the PHP error log via `error_log()` and never returned in HTTP responses.
