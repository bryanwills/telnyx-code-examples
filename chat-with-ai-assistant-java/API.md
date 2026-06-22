# API Reference — Chat With an AI Assistant

The JDK `HttpServer` (`Application.java`) exposes two HTTP routes. All responses are JSON.

## `POST /chat`

Send one user turn to the configured AI Assistant and return its reply. The optional
`conversation_id` threads multi-turn conversations: pass the value returned by the first
turn back on every follow-up turn. When omitted, the server generates a new UUID and
returns it.

### Request

`Content-Type: application/json`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | **yes** | The user's message text. Must be non-empty. |
| `conversation_id` | `string` | no | Stable id that threads the conversation. Omit on the first turn; reuse the returned value afterwards. |

```json
{
  "message": "What are your support hours?",
  "conversation_id": "0b6f2d4e-9a1c-4f3b-8e2a-1c2d3e4f5a6b"
}
```

### Response `200`

```json
{
  "assistant_id": "assistant-abc123",
  "conversation_id": "0b6f2d4e-9a1c-4f3b-8e2a-1c2d3e4f5a6b",
  "reply": "Our support team is available 24/7."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `assistant_id` | `string` | The assistant that produced the reply (from `TELNYX_ASSISTANT_ID`). |
| `conversation_id` | `string` | The conversation id to reuse on the next turn. |
| `reply` | `string` | The assistant's reply text. |

**Try it:**

```bash
curl -X POST http://localhost:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What are your support hours?"}'
```

---

## `GET /health`

Liveness probe.

### Response `200`

```json
{ "status": "ok" }
```

---

## Telnyx API endpoints called

The code calls the Telnyx AI Assistants API through the Java SDK:

| SDK call | Telnyx endpoint | Used by route |
|----------|-----------------|---------------|
| `client.ai().assistants().chat(assistantId, params)` | `POST /v2/ai/assistants/{assistant_id}/chat` | `POST /chat` |

`params` is an `AssistantChatParams` built with `.content(message)` and
`.conversationId(conversationId)`. The response is an `AssistantChatResponse` whose
`content()` accessor returns the assistant's reply as a `String`.

## Error Handling

All endpoints return JSON. Errors are mapped to HTTP status codes; underlying exception
details are logged server-side and never returned in the response body.

| Status | Meaning | Body |
|--------|---------|------|
| `200` | Success | Route-specific payload |
| `400` | Missing/empty `message` field | `{"error":"Missing required field: 'message'"}` |
| `405` | Wrong HTTP method for the route | `{"error":"Method not allowed"}` |
| `500` | `TELNYX_ASSISTANT_ID` not configured | `{"error":"Server is not configured"}` |
| `500` | Unexpected server error | `{"error":"Internal server error"}` |
| `502` | Telnyx API error (auth, rate limit, upstream status) | `{"error":"Upstream AI request failed"}` |
