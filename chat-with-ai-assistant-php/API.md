# API Reference

Typed reference for the HTTP routes exposed by `index.php` and the Telnyx API endpoints it calls.

## HTTP Endpoints

### `POST /chat`

Send a message to the AI Assistant identified by the `TELNYX_ASSISTANT_ID` environment variable and return its reply. Keeps conversation context via a `conversation_id`.

#### Request

```json
{
  "message": "What are your business hours?",
  "conversation_id": "conv-abcd1234"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | **yes** | The user message to send to the assistant. Must contain at least one non-whitespace character. |
| `conversation_id` | `string` | no | Existing conversation id to continue. If omitted, a new conversation is created and returned. |

> The assistant is chosen by the `TELNYX_ASSISTANT_ID` environment variable, not the request body.

#### Response `200`

```json
{
  "assistant_id": "assistant-1234abcd",
  "conversation_id": "conv-abcd1234",
  "user_message": "What are your business hours?",
  "reply": "We are open Monday to Friday, 9am to 5pm.",
  "timestamp": "2026-06-19T14:32:00+00:00"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `assistant_id` | `string` | ID of the assistant that handled the request |
| `conversation_id` | `string` | Conversation id to reuse on the next turn to keep context |
| `user_message` | `string` | Echo of the submitted `message` |
| `reply` | `string` | The assistant's reply (`$response->content` from the SDK) |
| `timestamp` | `string` | ISO 8601 (UTC) timestamp of when the response was built |

**Try it:**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your business hours?"}'
```

---

### `GET /health`

Liveness check. Takes no parameters.

#### Response `200`

```json
{ "status": "ok" }
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"` when the server is up |

---

### `POST /webhooks`

Receive an inbound Telnyx webhook. The handler verifies the Ed25519 signature with `$client->webhooks->unwrap($body, $headers)` before reading any fields, then reads event data from `data.payload`.

#### Request headers

| Header | Description |
|--------|-------------|
| `Telnyx-Signature-Ed25519` | Base64 Ed25519 signature of the payload |
| `Telnyx-Timestamp` | Unix timestamp; enforced against a 300s replay window |

The signed payload is `"{timestamp}|{raw_body}"`, verified against `TELNYX_PUBLIC_KEY`.

#### Response

| Status | Body | Meaning |
|--------|------|---------|
| `200` | `{"status":"received"}` | Signature valid; event acknowledged |
| `401` | `{"error":"Invalid webhook signature."}` | Signature verification failed |

---

## Telnyx API Endpoints Called

| Method | Path | SDK call | Purpose |
|--------|------|----------|---------|
| `POST` | `/v2/ai/conversations` | `$client->ai->conversations->create()` | Create a conversation when no `conversation_id` is supplied |
| `POST` | `/v2/ai/assistants/{assistant_id}/chat` | `$client->ai->assistants->chat(assistantID:, content:, conversationID:)` | Send the user message and receive the assistant's reply |

The chat call uses named parameters (`assistantID`, `content`, `conversationID`); the reply is read from `$response->content` (a `Telnyx\AI\Assistants\AssistantChatResponse`). See the [Chat with an Assistant API reference](https://developers.telnyx.com/api-reference/assistants/chat-with-an-assistant) for the full schema.

---

## Error Handling

All endpoints return JSON. On error: `{ "error": "Description of what went wrong" }`. Exception detail is logged via `error_log` server-side and never leaked to the client.

| Status | Meaning | Trigger | SDK exception |
|--------|---------|---------|---------------|
| `400` | Bad request | Invalid JSON or missing/empty `message` | — |
| `401` | Unauthorized | Invalid `TELNYX_API_KEY`; or invalid webhook signature | `Telnyx\Core\Exceptions\AuthenticationException`; `Telnyx\Core\Exceptions\WebhookException` |
| `429` | Rate limited | Account rate limit exceeded | `Telnyx\Core\Exceptions\RateLimitException` |
| `4xx`/`5xx` | API error | Other Telnyx API error (`$e->status` propagated; falls back to `502`) | `Telnyx\Core\Exceptions\APIException` |
| `500` | Server error | `TELNYX_ASSISTANT_ID` not set, or an unexpected error | — |
| `503` | Service unavailable | Network error reaching Telnyx | `Telnyx\Core\Exceptions\APIConnectionException` |
