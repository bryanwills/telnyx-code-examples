# API Reference — Chat With AI Assistant (Ruby)

Typed endpoint reference for the Sinatra service in `app.rb` and the Telnyx API it calls.

## Telnyx endpoint

### Chat with an Assistant

`POST /v2/ai/assistants/{assistant_id}/chat`

Called via the Ruby SDK as:

```ruby
CLIENT.ai.assistants.chat(
  assistant_id,            # String, positional
  content: "Hello",        # String, required — the user's message
  conversation_id: "conv-…", # String, required — reuse across turns for context
  name: "Caller"           # String, optional — display name of the speaker
)
```

**Path parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `assistant_id` | `string` | yes | The AI Assistant id (from `AI_ASSISTANT_ID`). Passed positionally. |

**Body parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | `string` | yes | The user's message text. |
| `conversation_id` | `string` | yes | Reuse the same id across turns to maintain conversation context. |
| `name` | `string` | no | Display name of the speaker. |

**Response** — `Telnyx::Models::AI::AssistantChatResponse`

| Field | Type | Description |
|-------|------|-------------|
| `content` | `string` | The assistant's reply text. (This is the only field on the response — there is no `data`, `messages`, or `assistant_id`.) |

```ruby
response = CLIENT.ai.assistants.chat(assistant_id, content: msg, conversation_id: cid)
response.content   # => "We are open Monday to Friday, 9am to 5pm."
```

---

## Service endpoints (this app)

### `POST /chat`

Send a message to the configured assistant and receive its reply.

**Request body** (`application/json`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | yes | The user's message. Must be non-empty / non-whitespace. |
| `conversation_id` | `string` | no | Reuse a previous response's id to keep context. If omitted, the server mints `conv-<uuid>`. |
| `name` | `string` | no | Display name of the speaker, forwarded to the assistant. |

**Success response** — `200 application/json`

| Field | Type | Description |
|-------|------|-------------|
| `assistant_id` | `string` | The assistant that answered (from `AI_ASSISTANT_ID`). |
| `conversation_id` | `string` | Pass this back on the next turn to maintain context. |
| `user_message` | `string` | Echo of the submitted message. |
| `assistant_response` | `string` | The assistant's reply (`response.content`). |

**Error responses** — `application/json` with `{ "error": "<message>" }`

| Status | Condition |
|--------|-----------|
| `400` | Invalid JSON body, missing `message`, or empty `message`. |
| `401` | Invalid Telnyx API key (`Telnyx::Errors::AuthenticationError`). |
| `429` | Rate limit exceeded (`Telnyx::Errors::RateLimitError`). |
| `500` | `AI_ASSISTANT_ID` not configured. |
| `502` | Unexpected upstream status from Telnyx. |
| `503` | Network error reaching Telnyx (`Telnyx::Errors::APIConnectionError`). |
| Telnyx status | Other `Telnyx::Errors::APIStatusError` HTTP statuses are passed through. |

### `POST /webhooks/ai`

Receive and verify an inbound Telnyx webhook. The Telnyx Ed25519 signature is
verified over `"<telnyx-timestamp>|<raw-body>"` before any field is read.

**Request headers**

| Header | Description |
|--------|-------------|
| `telnyx-signature-ed25519` | Base64 Ed25519 signature. |
| `telnyx-timestamp` | Unix seconds; rejected if older/newer than 300s. |

**Responses**

| Status | Condition |
|--------|-----------|
| `200` | `{ "received": true }` — signature valid; fields read from `data.payload`. |
| `400` | Missing signature headers. |
| `401` | Invalid signature. |
| `408` | Timestamp outside the allowed 300s window (replay protection). |
| `500` | `TELNYX_PUBLIC_KEY` not configured. |

### `GET /health`

Liveness check. Always returns `200 { "status": "ok" }`.
