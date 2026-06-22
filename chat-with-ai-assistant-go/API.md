# API Reference

Typed reference for the local Gin server and the Telnyx endpoints it calls.

## Local HTTP API

### `GET /health`

Liveness probe.

**Response — `200 OK`**

```json
{ "status": "ok" }
```

### `POST /chat`

Send one user turn to the configured AI assistant. Maintains multi-turn
context through a `conversation_id`.

**Request headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | yes | The user's message to the assistant. Must be non-empty. |
| `conversation_id` | `string` | no | Existing conversation thread id. Omit to start a new conversation; the server creates one and returns its id. |

```json
{
  "message": "What are your support hours?",
  "conversation_id": "8d1b...e2f"
}
```

**Response — `200 OK`**

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | `string` | The thread id. Echo this on the next request to keep context. |
| `reply` | `string` | The assistant's generated response. |

```json
{
  "conversation_id": "8d1b...e2f",
  "reply": "Our support team is available 24/7."
}
```

**Error responses**

| Status | Body | When |
|--------|------|------|
| `400 Bad Request` | `{ "error": "Invalid request body" }` | Body is not valid JSON. |
| `400 Bad Request` | `{ "error": "message is required" }` | `message` is empty or missing. |
| `4xx`/`5xx` | `{ "error": "Failed to start conversation" }` | The Conversations API rejected the request; status mirrors the upstream code. |
| `4xx`/`5xx` | `{ "error": "Failed to chat with assistant" }` | The Chat API rejected the request; status mirrors the upstream code. |

Error bodies never include raw exception or upstream response detail; the full
error is logged server-side only.

## Telnyx API endpoints used

### Create a Conversation

`POST https://api.telnyx.com/v2/ai/conversations`

Called on the first turn (when the client supplies no `conversation_id`) to
create a thread that carries context across turns.

**Go SDK call**

```go
conversation, err := client.AI.Conversations.New(ctx, telnyx.AIConversationNewParams{
    Metadata: map[string]string{"assistant_id": assistantID},
})
// conversation.ID is the conversation_id
```

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | no | Optional human-readable name for the conversation. |
| `metadata` | `map[string]string` | no | Arbitrary metadata. Set `ai_disabled: "true"` to create the thread with AI responses disabled. |

**Response — `200 OK`** — `Conversation`

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` (uuid) | The conversation id used on subsequent chat calls. |
| `created_at` | `string` (date-time) | When the conversation was created. |
| `last_message_at` | `string` (date-time) | Timestamp of the latest message. |
| `metadata` | `map[string]string` | Conversation metadata. |
| `name` | `string` | Conversation name, if set. |

### Chat with an Assistant

`POST https://api.telnyx.com/v2/ai/assistants/{assistant_id}/chat`

Sends a message to the assistant and returns its reply for the given
conversation.

**Go SDK call**

```go
resp, err := client.AI.Assistants.Chat(ctx, assistantID, telnyx.AIAssistantChatParams{
    Content:        message,
    ConversationID: conversationID,
})
// resp.Content is the assistant's reply
```

**Path parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `assistant_id` | `string` | yes | The assistant to chat with. |

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | `string` | yes | The message content sent by the client to the assistant. |
| `conversation_id` | `string` | yes | Unique identifier for the conversation thread, used to maintain context. |
| `name` | `string` | no | Optional display name of the user sending the message. |

**Response — `200 OK`** — `AIAssistantChatResponse`

| Field | Type | Description |
|-------|------|-------------|
| `content` | `string` | The assistant's generated response based on the input message and context. |
