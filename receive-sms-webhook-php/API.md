# API Reference — Receive SMS Webhook (PHP)

The vanilla PHP front controller (`index.php`) exposes two HTTP routes. All responses are JSON.

## `POST /webhooks/sms`

Receive a Telnyx inbound SMS webhook. This is the endpoint you register as the webhook URL on your Messaging Profile.

The handler reads the raw body via `file_get_contents('php://input')` and the headers via `getallheaders()`, then calls `$client->webhooks->unwrap($body, $headers)`. That helper:

1. Reads the `Telnyx-Signature-Ed25519` and `Telnyx-Timestamp` headers.
2. Enforces a 300-second timestamp tolerance (replay protection).
3. Rebuilds the signed payload exactly as `"<telnyx-timestamp>|<raw body>"`.
4. Verifies it with the base64 Ed25519 public key (`TELNYX_PUBLIC_KEY`) via `sodium_crypto_sign_verify_detached`.
5. Parses the verified JSON into a typed event object.

Only after verification succeeds are fields read — always from `data.payload`.

### Request

Telnyx sends the request; you do not call this endpoint yourself.

| Field | Type | Description |
|-------|------|-------------|
| Header `Telnyx-Signature-Ed25519` | `string` | Base64 Ed25519 signature over `"<timestamp>|<body>"` |
| Header `Telnyx-Timestamp` | `string` | Unix timestamp the event was signed at |
| Body | `application/json` | Telnyx v2 webhook envelope (`{ "data": { "event_type", "id", "payload": { ... } } }`) |

The inbound SMS event is read from the parsed object as:

| Source | SDK accessor | Description |
|--------|--------------|-------------|
| `data.event_type` | `$event->data->eventType` | `message.received` for inbound SMS |
| `data.payload.id` | `$event->data->payload->id` | Message ID |
| `data.payload.from` | `$event->data->payload->from->phoneNumber` | Sender number (+E.164) |
| `data.payload.to[0]` | `$event->data->payload->to[0]->phoneNumber` | Your receiving number (+E.164) |
| `data.payload.text` | `$event->data->payload->text` | Message body |
| `data.payload.received_at` | `$event->data->payload->receivedAt` | ISO-8601 receipt time |

### Responses

| Status | Meaning | Body |
|--------|---------|------|
| `200` | Signature valid, inbound SMS processed | `{"status": "received", "messageId": "..."}` |
| `200` | Signature valid, non-`message.received` event ignored | `{"status": "ignored", "eventType": "..."}` |
| `200` | Signature valid, processing error swallowed to avoid Telnyx retries | `{"status": "error"}` |
| `400` | Body could not be parsed as a Telnyx event | `{"error": "Bad webhook request"}` |
| `401` | Missing or invalid Ed25519 signature | `{"error": "Invalid webhook signature"}` |
| `500` | `TELNYX_API_KEY` / `TELNYX_PUBLIC_KEY` not set | `{"error": "Server misconfigured"}` |

**Response `200` (processed):**

```json
{
  "status": "received",
  "messageId": "40000000-0000-0000-0000-000000000000"
}
```

---

## `GET /health`

Liveness probe. No client or credentials required.

### Response `200`

```json
{ "status": "ok" }
```

---

## Telnyx SDK calls

| SDK call | Purpose | Used by route |
|----------|---------|---------------|
| `new Telnyx\Client(apiKey: ..., publicKey: ...)` | Construct the client; `publicKey` enables webhook verification | startup |
| `$client->webhooks->unwrap($body, $headers)` | Verify the Ed25519 signature and parse the event | `POST /webhooks/sms` |

## Error Handling

Webhook verification failures throw `Telnyx\Core\Exceptions\WebhookException`, which is mapped to `401`. Any other parse/processing error is logged via `error_log()` and surfaced as a generic message; raw exception details are never returned to the client.
