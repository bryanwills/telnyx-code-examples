## `GET /`

Admin UI — a single-page HTML app with model dropdown, chat panel, and stats.

### Response `200`

Returns `text/html` with the admin UI pre-loaded with the active model from KV.

---

## `GET /model`

Get the active model and available models.

### Response `200`

```json
{
  "model": "moonshotai/Kimi-K2.6",
  "models": [
    { "id": "moonshotai/Kimi-K2.6", "name": "Kimi K2.6", "vendor": "Moonshot AI" },
    { "id": "zai-org/GLM-5.2", "name": "GLM-5.2", "vendor": "Zhipu AI" },
    { "id": "meta-llama/Llama-3.3-70B-Instruct", "name": "Llama 3.3 70B", "vendor": "Meta" }
  ]
}
```

---

## `POST /model`

Switch the active model by writing to KV. Takes effect immediately for the next message — no redeploy.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | `string` | **yes** | Model ID (must be in the available models list) |

**Try it:**

```bash
curl -X POST https://multi-model-inference-switcher-<id>.telnyxcompute.com/model \
  -H "Content-Type: application/json" \
  -d '{"model":"zai-org/GLM-5.2"}'
```

### Response `200`

```json
{
  "model": "zai-org/GLM-5.2",
  "stored": "kv"
}
```

---

## `POST /chat`

Send a message and get a reply from the active model. The model is read from KV at call time.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `string` | **yes** | The user's message |

**Try it:**

```bash
curl -X POST https://multi-model-inference-switcher-<id>.telnyxcompute.com/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"What is 2+2?"}'
```

### Response `200`

```json
{
  "reply": "4",
  "model": "moonshotai/Kimi-K2.6"
}
```

---

## `GET /history`

Get conversation history and usage stats.

### Response `200`

```json
{
  "messages": [
    { "role": "user", "content": "What is 2+2?" },
    { "role": "assistant", "content": "4", "model": "varies" }
  ],
  "totalRequests": 1,
  "modelUsage": {
    "moonshotai/Kimi-K2.6": 1
  }
}
```

---

## `POST /clear`

Clear the conversation history.

### Response `200`

```json
{
  "action": "cleared"
}
```

---

## `GET /debug/state`

Inspect the actor's durable state plus the active model from KV.

### Response `200`

```json
{
  "sessionId": "default",
  "totalRequests": 3,
  "modelUsage": {
    "moonshotai/Kimi-K2.6": 2,
    "zai-org/GLM-5.2": 1
  },
  "activeModel": "zai-org/GLM-5.2",
  "kvNamespace": "d02b98e3-..."
}
```

---

## `GET /health/{liveness,readiness}`

Health check endpoints.

### Response `200`

```
ok
```
