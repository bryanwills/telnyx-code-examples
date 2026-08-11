# Build an SMS Support Agent with Follow-Up

SMS support agent on Telnyx Edge Compute + Agent SDK — answer SMS questions via LLM and schedule a 24h follow-up check-in. Uses the `[telnyx]` binding for zero-credential SMS and inference.

## How It Works

```
  Inbound SMS → webhook → SupportAgent.receive()
        │
        ▼
  ┌──────────────────────────────────────┐
  │ Agent SDK (Stateful Actor)            │
  │  1. this.messages.add("user", text)   │
  │  2. this.queue("process")             │
  │  3. process():                        │
  │     → this.messages.toOpenAI()        │
  │     → env.TELNYX.ai.openai.chat       │
  │     → this.messages.add("assistant")  │
  │     → env.TELNYX.messages.send()      │
  │     → this.schedule(24h, "followup") │
  │  4. followup():                       │
  │     → check if customer replied      │
  │     → if not, send check-in SMS       │
  └──────────────────────────────────────┘
```

## Telnyx Products Used

- **Edge Compute (Agent SDK)** — `Agent` base class from `@telnyx/edge-runtime` extends `StatefulActor` with message history, scheduled tasks, and durable state
- **AI Inference** — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated `[telnyx]` binding)
- **Messaging** — via `this.env.TELNYX.messages.send()` (pre-authenticated `[telnyx]` binding)

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- A Telnyx phone number with a messaging profile (for real SMS)

## Step 1: Understand the Code

### `src/supportAgent.ts` — The Agent

```typescript
export class SupportAgent extends Agent<SupportEnv, SupportState> {
  async receive({ text, from, to }) {
    await this.setState({ from, to });
    await this.messages.add("user", text);  // durable history
    await this.queue("process");             // background turn
  }

  async process() {
    const history = await this.messages.toOpenAI();
    const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
      model: "zai-org/GLM-5.2",
      messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history],
    });
    const reply = completion.choices[0].message.content;
    await this.messages.add("assistant", reply);
    await this.env.TELNYX.messages.send({ from: state.to, to: state.from, text: reply });
    await this.schedule(86400, "followup", null, { id: `followup-${state.from}` });
  }

  async followup() {
    const last = await this.messages.last();
    if (last?.role !== "assistant") return; // customer replied — skip
    await this.env.TELNYX.messages.send({ from: state.to, to: state.from, text: "Did that solve your problem?" });
  }
}
```

### `src/index.ts` — The Front Door

Routes inbound SMS webhooks to the per-phone-number actor:

```typescript
if (evt.event_type === "message.received") {
  await env.SUPPORT.idFromName(actorName(from)).receive({ text, from, to });
  return Response.json({ action: "queued" });
}
```

Also provides `/debug/message` for testing without a messaging profile.

### `telnyx.toml` — Config

```toml
[[actors]]
binding = "SUPPORT"
type = "SupportAgent"

[telnyx]
binding = "TELNYX"  # pre-authenticated client — no API key in code
```

### Agent SDK Primitives

| Primitive | Method | Purpose |
|-----------|--------|---------|
| Message History | `this.messages.add()` / `.toOpenAI()` / `.last()` | Durable conversation log per phone number |
| Scheduled Tasks | `this.queue()` / `this.schedule()` | Background processing + 24h follow-up |
| Durable State | `this.setState()` / `this.getState()` | Per-conversation state |
| Telnyx Binding | `this.env.TELNYX.*` | Zero-credential SMS + inference |

## Step 2: Deploy

```bash
npm install
telnyx-edge ship
```

## Step 3: Test

### Health

```bash
curl https://sms-support-agent-<id>.telnyxcompute.com/health/liveness
```

### Simulate inbound SMS (no real number needed)

```bash
curl -X POST https://sms-support-agent-<id>.telnyxcompute.com/debug/message \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","to":"+16282564655","text":"How do I send an SMS?"}'
```

### Real SMS (requires messaging profile)

1. Point your messaging profile webhook to `https://sms-support-agent-<id>.telnyxcompute.com/webhooks/sms`
2. Send an SMS from your phone to your Telnyx number
3. The agent will reply via SMS within ~5 seconds

## Going to Production

- **Webhook signature verification** — verify the `telnyx-signature-ed25519` header before processing
- **Idempotent sends** — task delivery is at-least-once; dedup outbound SMS by stable message ID
- **Multi-language** — detect language and route to a language-specific system prompt
- **Human handoff** — add a tool that escalates to a human when the LLM can't answer
- **Rate limiting** — per-phone-number rate limits to prevent abuse
- **Cost tracking** — track tokens used per conversation in state
- **Dashboard** — add a WebSocket desk for live monitoring (Agent SDK supports `onConnect`)

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sms-support-agent-with-followup/README.md)
- [Agent SDK Overview](https://developers.telnyx.com/docs/agent-sdk)
- [Agent SDK Quickstart](https://developers.telnyx.com/docs/agent-sdk/quickstart)
- [Roll Your Own Agent](https://developers.telnyx.com/docs/agent-sdk/examples/roll-your-own)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
