# Build a Multi-Model Inference Switcher

Switch between LLM models at runtime via a KV feature flag — no redeploy. The active model is read from KV at inference time, and an admin UI lets you toggle it live.

## How It Works

```
  POST /chat → SwitcherAgent.process(text, model)
        │
        ▼
  ┌──────────────────────────────────────────────────────┐
  │ Agent SDK (Stateful Actor)                            │
  │                                                      │
  │  1. Read active model from KV:                        │
  │     → GET /v2/storage/kvs/<ns>/keys/active-model      │
  │  2. Inference with the active model:                  │
  │     → env.TELNYX.ai.openai.chat.createCompletion({     │
  │         model, messages                                │
  │       })                                               │
  │  3. Store reply in durable history                    │
  │  4. Return reply + model name                         │
  └──────────────────────────────────────────────────────┘

  Admin UI (GET /):
    → Model dropdown → POST /model → writes KV → live switch
    → Chat panel → POST /chat → reads KV → inference → reply
```

## Telnyx Products Used

- **Edge Compute (Agent SDK)** — `Agent` base class with durable conversation history and state
- **AI Inference** — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated `[telnyx]` binding)
- **KV Storage** — via REST API for the model feature flag (global, not per-actor)

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+

## Step 1: Understand the Code

### `src/switcherAgent.ts` — The Agent

```typescript
export class SwitcherAgent extends Agent<SwitcherEnv, SwitcherState> {
  async process(text: string, model: string) {
    await this.messages.add("user", text);
    const history = await this.messages.toOpenAI();

    const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
      model,  // ← from KV, not hardcoded
      messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history],
      max_tokens: 2000,
    });
    const reply = completion.choices[0].message.content;

    await this.messages.add("assistant", reply);
    return { reply, model };
  }
}
```

### `src/index.ts` — The Front Door

Reads the active model from KV, passes it to the actor, and serves the admin UI:

```typescript
// Read model from KV
const activeModel = await getActiveModel(kvNamespaceId, apiKey);

// Call the actor with the KV-selected model
const result = await env.SWITCHER.idFromName("default").process(text, activeModel);

// Serve admin UI at GET /
if (url.pathname === "/") {
  return new Response(ADMIN_HTML, { headers: { "Content-Type": "text/html" } });
}
```

### `telnyx.toml` — Config

```toml
[[actors]]
binding = "SWITCHER"
type = "SwitcherAgent"

[telnyx]
binding = "TELNYX"  # pre-authenticated inference — no API key in code

[[secrets]]
binding = "TELNYX_API_KEY"
name = "TELNYX_API_KEY"  # for KV REST API

[env_vars]
KV_NAMESPACE_ID = "<your-kv-namespace-id>"
```

### Agent SDK Primitives

| Primitive | Method | Purpose |
|-----------|--------|---------|
| Message History | `this.messages.add()` / `.toOpenAI()` | Durable conversation log |
| Durable State | `this.setState()` / `this.getState()` | Usage stats, model counts |
| Telnyx Binding | `this.env.TELNYX.ai.openai.chat.createCompletion()` | Zero-credential inference |
| KV (REST API) | `GET/PUT /v2/storage/kvs/<ns>/keys/<key>` | Global model feature flag |

## Step 2: Create KV namespace and seed

```bash
telnyx-edge storage kv create --name "switcher-flag"
# Copy the KV ID

telnyx-edge storage kv key put <kv-id> active-model moonshotai/Kimi-K2.6
```

## Step 3: Deploy

```bash
npm install
telnyx-edge ship
```

## Step 4: Open the admin UI

Open the deployed URL in your browser. You'll see:

- **Model dropdown** with the active model pre-selected
- **Switch button** to toggle the model (writes to KV instantly)
- **Chat panel** to send messages and see replies tagged with the model used
- **Stats** showing total requests and models used

## Step 5: Test the live switch

1. Send a message with Kimi K2.6 → reply is tagged "Kimi K2.6"
2. Switch to GLM-5.2 via the dropdown → KV updates instantly
3. Send another message → reply is tagged "GLM-5.2"
4. Switch to Llama 3.3 70B → send a message → tagged "Llama 3.3 70B"

The switch happens without any redeploy — just a KV write.

## Going to Production

- **Per-user models** — key the KV flag by user ID instead of a global flag
- **A/B testing** — route a percentage of traffic to each model via KV
- **Fallback** — if the active model fails, fall back to a secondary model
- **Cost tracking** — track tokens per model in actor state
- **Rate limiting** — per-model rate limits to control costs
- **WebSocket** — for real-time model updates without polling

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/multi-model-inference-switcher/README.md)
- [Agent SDK Overview](https://developers.telnyx.com/docs/agent-sdk)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Telnyx Developer Docs](https://developers.telnyx.com)
