# API Reference — Run LLM Inference

This service exposes three HTTP routes from `server.js`. All requests and responses are JSON.

## `GET /health`

Liveness check. Returns the configured default model.

### Request

No body.

### Response `200`

```json
{
  "status": "ok",
  "model": "meta-llama/Llama-3.3-70B-Instruct"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `"ok"` when the server is up |
| `model` | `string` | The default model from `AI_MODEL` |

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## `POST /inference/chat`

Run a full chat completion. Forwards `messages` and generation parameters to the Telnyx Inference API and returns the raw response.

### Request

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a haiku about the ocean."}
  ],
  "model": "meta-llama/Llama-3.3-70B-Instruct",
  "max_tokens": 200,
  "temperature": 0.7
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | `array<object>` | **yes** | OpenAI-compatible message list. Each item has `role` (`system`/`user`/`assistant`) and `content` (`string`) |
| `model` | `string` | no | Model slug. Defaults to `AI_MODEL` (`meta-llama/Llama-3.3-70B-Instruct`) |
| `max_tokens` | `number` | no | Maximum tokens to generate. Defaults to `500` |
| `temperature` | `number` | no | Sampling temperature. Defaults to `0.7` |

### Response `200`

Returns the raw Telnyx chat completion object.

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "model": "meta-llama/Llama-3.3-70B-Instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Vast and endless blue\nWaves whisper to the shoreline\nMoonlight on the deep"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 23,
    "completion_tokens": 18,
    "total_tokens": 41
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Completion identifier |
| `model` | `string` | Model that produced the completion |
| `choices` | `array<object>` | Generated choices; `choices[0].message.content` holds the text |
| `usage` | `object` | Token accounting (`prompt_tokens`, `completion_tokens`, `total_tokens`) |

**Try it:**

```bash
curl -X POST http://localhost:5000/inference/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Write a haiku about the ocean."}]}'
```

---

## `POST /inference/ask`

Ask a single question and get just the answer text back. Internally builds a `messages` array (optional `system_prompt` first, then the question) and returns `choices[0].message.content`.

### Request

```json
{
  "question": "What is the capital of France?",
  "system_prompt": "Answer in one word."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `string` | **yes** | The user question to send to the model |
| `system_prompt` | `string` | no | System instruction prepended to the conversation |

### Response `200`

```json
{
  "answer": "Paris."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `answer` | `string` | The model's text reply (`choices[0].message.content`) |

**Try it:**

```bash
curl -X POST http://localhost:5000/inference/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the capital of France?"}'
```

---

## Telnyx API Endpoints Called

The app calls one upstream endpoint:

- **Chat Completions**: `POST https://api.telnyx.com/v2/ai/chat/completions` — authenticated with `Authorization: Bearer ${TELNYX_API_KEY}`. The request body sends `model`, `messages`, `max_tokens`, and `temperature`. -- [API reference](https://developers.telnyx.com/api/inference/inference-embedding/post-chat-completions)

---

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing `messages` (chat) or `question` (ask) |
| `500` | Server error — upstream Inference API failure (e.g. `Inference API error: 401`) |
