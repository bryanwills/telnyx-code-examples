# Guide: LangGraph Agent on Edge

A standalone tutorial for running a LangGraph `StateGraph` inside the Telnyx Agent SDK on Edge Compute with zero-credential LLM inference.

## What you'll build

An SMS support agent that:

1. Receives an SMS webhook from a customer
2. Classifies the message intent (order vs. smalltalk) using a LangGraph node
3. Looks up order status if the intent is "order"
4. Composes a reply using another LangGraph node
5. Sends the reply via the pre-authenticated Telnyx API binding (no API key)
6. Schedules a 24-hour follow-up nudge

## Key concepts

### The zero-credential adapter

The Telnyx API binding (`this.env.TELNYX`) is pre-authenticated at the edge — no API key in your code. But LangGraph nodes call the LLM through a `BaseChatModel`. The stock `ChatOpenAI` requires an `apiKey` and `baseURL`.

This sample ships `TelnyxBoundChatModel` — a minimal `SimpleChatModel` subclass that calls `this.env.TELNYX.ai.openai.chat.createCompletion()` under the hood:

```typescript
class TelnyxBoundChatModel extends SimpleChatModel {
  async _call(messages: BaseMessage[]): Promise<string> {
    const mapped = messages.map(m => ({ role: roleForMessage(m), content: ... }));
    const res = await this.env.TELNYX.ai.openai.chat.createCompletion({
      model: this.model,
      messages: mapped,
    });
    return res.choices[0].message.content;
  }
}
```

This is the key innovation: LangGraph gets its chat-model interface, and you get zero-credential inference. No `TELNYX_API_KEY` in code, bundle, or logs.

### The turn state machine

At-least-once delivery means a crash can retry `process()`. The turn state machine prevents duplicates:

```
receive() → turn=1, queuedTurn=1, queue("process")
process() → targetTurn=1, lastSentTurn=0 → run graph → stage pendingOutbound → send → lastSentTurn=1
```

If two inbound messages arrive before `process()` runs:
```
receive() → turn=1, queuedTurn=1, queue("process")
receive() → turn=2, queuedTurn=2, queue("process")
process() → targetTurn=2 (latest) → run graph → send → lastSentTurn=2
process() → targetTurn=2 ≤ lastSentTurn=2 → NO-OP (stale)
```

### Three state layers

Don't conflate these:

1. **LangGraph graph state** — `intentLabel`, `actionResult`, `replyText` — ephemeral, one `process()` run
2. **Agent SDK durable state** — `turn`, `queuedTurn`, `lastSentTurn` — survives restarts, per actor
3. **Agent SDK message history** — `this.messages` — the conversation log, per actor

## Step-by-step

### 1. The adapter (`src/telnyx-bound-chat-model.ts`)

The `TelnyxBoundChatModel` extends `SimpleChatModel` from `@langchain/core`. It maps LangChain `BaseMessage[]` to `{role, content}[]` and calls the binding.

Key: the adapter takes `{ env, model }` in its constructor. The actor owns `this.env`, so the adapter is constructed inside `process()`.

### 2. The graph (`src/graph.ts`)

A 3-node `StateGraph` with typed channels:

```typescript
const GraphState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({ reducer: (_, y) => y }),
  intentLabel: Annotation<Intent>(),
  actionResult: Annotation<string>(),
  replyText: Annotation<string>(),
});

const graph = new StateGraph(GraphState)
  .addNode("intent", intentNode)     // LLM classify
  .addNode("action", actionNode)     // plain TS lookup
  .addNode("response", responseNode) // LLM compose
  .addEdge(START, "intent")
  .addConditionalEdges("intent", s => s.intentLabel === "order" ? "action" : "response")
  .addEdge("action", "response")
  .addEdge("response", END)
  .compile();
```

> **Important:** LangGraph node names cannot match state channel names. Use `intentLabel` (not `intent`) as the channel, `intent` as the node.

### 3. The actor (`src/conversation.ts`)

`Conversation extends Agent<Env, ConvState>` with the turn state machine:

- `receive()` — adds user message, bumps turn, queues `process()`. No LLM calls (30s budget).
- `process()` — stale-task guard, runs graph, stages `pendingOutbound`, sends SMS, commits `lastSentTurn`.
- `nudge()` — checks if customer replied; if not, sends a follow-up.

### 4. The webhook handler (`src/index.ts`)

Verifies the Ed25519 signature using the `telnyx` SDK's `webhooks.unwrap()`, then routes to the actor by phone number:

```typescript
await env.CONVOS.idFromName(actorNameForPhone(from)).receive({ text, from, to, eventId });
```

### 5. Deploy

```bash
telnyx-edge types   # generate Env types from telnyx.toml
telnyx-edge ship     # deploy to edge
```

Point your messaging profile webhook at the function URL. Send an SMS. Get a reply.

## Next steps

- Swap the stubbed `lookupOrder` for a real database query (use the actor's embedded SQL: `this.ctx.storage.sql.exec()`)
- Add tool-calling with `createReactAgent` (requires a `bindTools`-capable adapter)
- Add web-chat over WebSocket (the Agent SDK supports `onConnect`)
- Deploy to production with `SMS_TRANSPORT=production` and a real Telnyx number
