# LangGraph Agent on Edge

A LangGraph `StateGraph` (intent → action → response) running inside the Telnyx Agent SDK on Edge Compute, with zero-credential LLM inference via the pre-authenticated Telnyx API binding.

## Why Telnyx

Telnyx is AI Communications Infrastructure — a single platform for voice, SMS, and AI inference. This example demonstrates how Edge Compute's Agent SDK provides the durable substrate (message history, state, scheduled tasks) while LangGraph provides the reasoning loop, all with zero-credential inference through the Telnyx API binding.

## Telnyx API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `POST /v2/messages` (via binding) | Send outbound SMS replies to the customer |
| `POST /v2/ai/openai/chat/completions` (via binding) | Zero-credential LLM inference for the LangGraph nodes |
| `GET /v2/public_key` | Fetch the Ed25519 public key for webhook signature verification |
| `message.received` webhook | Inbound SMS webhook that triggers the agent |

## Architecture

```
SMS webhook (message.received)
  └─> src/index.ts fetch()
        • verify Ed25519 signature via telnyx SDK
        • route to Conversation actor by phone number
        • return 200 immediately (30s budget)

  Conversation.receive()              ← inbound, ~ms
        • add user message to history
        • bump turn counter
        • queue("process") → ack webhook

  Conversation.process()              ← queued task, minutes of budget
        • stale-task no-op guard (turn ≤ lastSentTurn → return)
        • this.messages.toLangChain() → history
        • LangGraph StateGraph: intent → action → response
              intent   : TelnyxBoundChatModel.classify(history)
              action   : lookupOrder(orderId) — plain TS
              response : TelnyxBoundChatModel.reply(history, actionResult)
        • stage pendingOutbound → send SMS → commit lastSentTurn
        • re-queue if newer turn arrived during processing
        • schedule 24h nudge

  TelnyxBoundChatModel                ← the zero-credential adapter
        • extends SimpleChatModel (LangChain)
        • _call() maps messages → {role, content}[]
        • calls this.env.TELNYX.ai.openai.chat.createCompletion()
        • no API key in code, bundle, or logs
```

### Three state layers (the key concept)

| Layer | API | Scope | Used for |
|-------|-----|-------|----------|
| LangGraph graph state | `StateGraph` channels | Ephemeral, one `process()` run | `intentLabel`, `actionResult`, `replyText` |
| Agent SDK durable state | `this.setState()` / `this.getState()` | Durable, per actor | `turn`, `queuedTurn`, `lastSentTurn`, `pendingOutbound` |
| Agent SDK message history | `this.messages.add()` / `.toLangChain()` | Durable, per actor | The conversation log |

### Turn state machine (at-least-once safety)

The turn state machine prevents duplicate replies under retry and concurrent inbound messages:

| Field | Purpose |
|-------|---------|
| `turn` | Monotonic counter, incremented on each inbound |
| `queuedTurn` | The turn we want `process()` to handle next |
| `processingTurn` | The turn currently being processed |
| `lastSentTurn` | Highest turn for which SMS send resolved successfully |
| `pendingOutbound` | Staging record `{turn, reply, clientRef}` before send |

**Stale-task no-op:** if `queuedTurn ≤ lastSentTurn`, `process()` returns immediately.
**Per-turn idempotency:** the guard is on `turn`, not reply text, so identical legitimate replies across different turns are not suppressed.

> **At-least-once note:** Telnyx `POST /messages` does not expose a wire-side idempotency key. A crash in the sub-millisecond window between send-ack and `setState({lastSentTurn})` can produce one duplicate. The `lastSentTurn` commit is the last durable write after send to minimize this window.

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `TELNYX_API_KEY` | Fetch the Ed25519 public key for webhook verification. NOT used for LLM inference. | Yes (production) |
| `TELNYX_PUBLIC_KEY` | Ed25519 public key stored as an Edge secret. Fetched via `telnyx-edge secrets add`. | Yes (production) |
| `MODEL` | LLM model ID. Docs-indicated default: `zai-org/GLM-5.2`. Must be a model the binding serves. | No (defaults to `zai-org/GLM-5.2`) |
| `DEMO_MODE` | `"true"` serves a local HTML test UI at `/`. `"false"` disables it. | No (defaults to `true`) |
| `SMS_TRANSPORT` | `"demo"` simulates outbound SMS in the event log. `"production"` sends real SMS via the binding. | No (defaults to `demo`) |
| `DEMO_FROM_NUMBER` | The agent's phone number (E.164) for the demo UI. | No (defaults to `+15557654321`) |
| `DEMO_SENDER_NUMBER` | The simulated customer's phone number (E.164) for the demo UI. | No (defaults to `+15551234567`) |

> **Which secrets do I need?** You need `TELNYX_PUBLIC_KEY` (for webhook signature verification). You do NOT need an inference `TELNYX_API_KEY` — the Edge binding is pre-authenticated. "Zero-credential" means no inference API key in code, bundle, or logs.

## Setup

### 1. Clone and install

```bash
cd telnyx-code-examples/langgraph-agent-on-edge
npm install
```

### 2. Fetch the public key and store it as a secret

```bash
PUBLIC_KEY=$(curl -s -H "Authorization: Bearer $TELNYX_API_KEY" \
  https://api.telnyx.com/v2/public_key | jq -r '.data.public')

telnyx-edge secrets add TELNYX_PUBLIC_KEY "$PUBLIC_KEY"
```

### 3. Run the demo locally

```bash
npm run typecheck   # verify TypeScript compiles
npm test             # run the test suite (28 tests)
```

### 4. Deploy to Edge Compute

```bash
# Scaffold a function ID (first time only):
telnyx-edge new-func --actor --name=langgraph-agent-on-edge

# Update telnyx.toml with the generated func_id, then:
telnyx-edge types   # generate binding types
telnyx-edge ship     # deploy
```

### 5. Smoke test the model (deploy-time verification)

After `telnyx-edge ship`, verify the binding serves the configured model before pointing real SMS traffic:

```bash
# Option A: demo mode smoke — hit the demo UI at the function URL, send "where is order ORD-10042?"
# Option B: production smoke — send a real SMS to your Telnyx number with the same text
```

**If the smoke returns a 422 / model-not-found**, the binding doesn't serve `MODEL` with that exact ID. Switch to the FP8 variant and re-ship:

```bash
# Edit telnyx.toml [env_vars] or set the secret:
MODEL=zai-org/GLM-5.2-FP8
telnyx-edge ship
# rerun the smoke
```

| Model ID | When to use |
|----------|-------------|
| `zai-org/GLM-5.2` | Default. Telnyx's Available Models docs list this as a Chat Completions model. Try this first. |
| `zai-org/GLM-5.2-FP8` | Fallback if `zai-org/GLM-5.2` returns 422 on the binding. |

This is a runtime model-string verification, not a deployment blocker. `MODEL` is configurable via env var — no code change needed to switch.

### 6. Point the SMS webhook

In the Telnyx Mission Control Portal, set your messaging profile's webhook URL to:
```
https://langgraph-agent-on-edge-<your-org>.telnyxcompute.com/webhooks/messaging
```

### 7. Test

- **Demo mode:** Visit the function URL in your browser for a local HTML chat UI.
- **Production:** Send an SMS to your Telnyx number with "where is order ORD-10042?" and receive a reply.

## API Reference

See [API.md](API.md) for the full typed endpoint reference.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `TELNYX_PUBLIC_KEY is required` | Run `telnyx-edge secrets add TELNYX_PUBLIC_KEY` and re-ship. |
| Webhook returns 401 | Signature verification failed. Ensure the public key matches your org's key from `GET /v2/public_key`. |
| No SMS reply in demo mode | `SMS_TRANSPORT=demo` simulates sends in the event log. Set `SMS_TRANSPORT=production` for real SMS. |
| Model returns 422 | The model ID in `MODEL` may not be served by the binding. Default is `zai-org/GLM-5.2`; fallback is `zai-org/GLM-5.2-FP8`. Set `MODEL` env var and re-ship. See [Smoke test the model](#5-smoke-test-the-model-deploy-time-verification). |
| Duplicate SMS on retry | This is the at-least-once window (see Architecture). The `lastSentTurn` guard minimizes it. |

## Related Examples

- [agent-with-tool-calling](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/agent-with-tool-calling/README.md) — Agent SDK with LLM tool calling (ReAct pattern)
- [multi-turn-sms-quiz-agent](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/multi-turn-sms-quiz-agent/README.md) — Multi-turn SMS quiz with durable state
- [sentiment-analysis-agent](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sentiment-analysis-agent/README.md) — Sentiment analysis with the Agent SDK

## Resources

- [Agent SDK docs](https://developers.telnyx.com/docs/agent-sdk) — the `Agent` base class, message history, state, and scheduled tasks
- [Calling LLMs](https://developers.telnyx.com/docs/agent-sdk/concepts/calling-llms) — both wiring patterns (roll your own + bring a framework)
- [LangGraph Agent example](https://developers.telnyx.com/docs/agent-sdk/examples/langgraph) — the official docs example (uses ChatOpenAI+key; this sample improves on it with the zero-credential binding)
- [Edge Compute quickstart](https://developers.telnyx.com/docs/edge-compute/quickstart) — getting started with Edge functions
- [Telnyx API binding](https://developers.telnyx.com/docs/edge-compute/telnyx-api) — pre-authenticated Telnyx client for your function
- [Webhook signing](https://developers.telnyx.com/docs/development/api-fundamentals/webhooks/receiving-webhooks) — Ed25519 signature verification
- [Telnyx SDK](https://developers.telnyx.com/development/sdk) — official SDKs for all languages
- [AI Communications Infrastructure](https://telnyx.com) — Telnyx product page
- [Pricing](https://telnyx.com/pricing) — Telnyx pricing

## Agent Discovery

This example is designed for agents and search systems that need a compact description of the runnable project:

- **Use case**: LangGraph StateGraph (intent → action → response) running inside the Telnyx Agent SDK on Edge Compute with zero-credential LLM inference via the Telnyx API binding.
- **Runtime**: Node.js on Telnyx Edge Compute Stateful Actors (Agent SDK).
- **Primary APIs**: Telnyx Inference (via pre-authenticated binding), Telnyx Messaging (SMS via binding), actor-local SQL for process logging, Ed25519 webhook verification.
- **Entry point**: `src/index.ts` — fetch handler that verifies signatures and routes to the `Conversation` actor by phone number.
- **Graph**: `src/graph.ts` — 3-node `StateGraph` (intent → action → response) with conditional routing; `intent` and `response` nodes call `TelnyxBoundChatModel`, `action` is plain TS.
- **Turn state machine**: `src/conversation.ts` — per-turn counters (`turn`, `queuedTurn`, `processingTurn`, `lastSentTurn`, `pendingOutbound`) for at-least-once SMS safety under retry and concurrent inbound.
- **Zero-credential adapter**: `src/telnyx-bound-chat-model.ts` — `SimpleChatModel` subclass that calls `this.env.TELNYX.ai.openai.chat.createCompletion()` (no API key in code, bundle, or logs).
