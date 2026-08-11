---
name: sms-support-agent-with-followup
title: "SMS Support Agent with Follow-Up"
description: "SMS support agent on Telnyx Edge Compute + Agent SDK — answer SMS questions via LLM and schedule a 24h follow-up check-in. No API key in code."
language: nodejs
framework: telnyx-edge (Agent SDK)
telnyx_products: [Edge Compute, Messaging, AI Inference]
---

# SMS Support Agent with Follow-Up

SMS support agent on Telnyx Edge Compute + Agent SDK — answer SMS questions via LLM and schedule a 24h follow-up check-in. Uses the `[telnyx]` binding for zero-credential SMS and inference — no API key anywhere in code.

## Telnyx API Endpoints Used

- **AI Inference**: `POST /v2/ai/openai/chat/completions` — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated binding)
- **Messaging**: `POST /v2/messages` — via `this.env.TELNYX.messages.send()` (pre-authenticated binding)

## Architecture

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

## Environment Variables / Secrets

No API key needed in code — the `[telnyx]` binding in `telnyx.toml` carries auth for both inference and messaging.

```toml
[telnyx]
binding = "TELNYX"
```

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `[telnyx]` binding | toml | **yes** | Pre-authenticated Telnyx client (inference + messaging) |

## Setup

### Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- A Telnyx phone number with a messaging profile (for real SMS)

### 1. Deploy

```bash
npm install
telnyx-edge ship
```

`ship` prints a URL like `sms-support-agent-<id>.telnyxcompute.com`.

### 2. Point your messaging profile webhook

In the [Telnyx Portal](https://portal.telnyx.com/messaging/profiles):
1. Create or edit a Messaging Profile assigned to your Telnyx number
2. Set the **Webhook URL** → `https://sms-support-agent-<id>.telnyxcompute.com/webhooks/sms`

### 3. Test

```bash
# Health check
curl https://sms-support-agent-<id>.telnyxcompute.com/health/liveness

# Simulate an inbound SMS (no real number needed)
curl -X POST https://sms-support-agent-<id>.telnyxcompute.com/debug/message \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","to":"+16282564655","text":"How do I send an SMS?"}'
```

## API Reference

### `POST /webhooks/sms`

Receives Telnyx `message.received` webhooks. Routes to the per-phone-number actor.

### `POST /debug/message`

Simulate an inbound SMS without a messaging profile (for testing).

```bash
curl -X POST https://sms-support-agent-<id>.telnyxcompute.com/debug/message \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","to":"+16282564655","text":"How do I send an SMS?"}'
```

**Response:**

```json
{
  "action": "queued",
  "from": "+17177247292",
  "to": "+16282564655"
}
```

### `GET /health/{liveness,readiness}`

Health checks.

```bash
curl https://sms-support-agent-<id>.telnyxcompute.com/health/liveness
```

## How It Works

1. **Inbound SMS** → Telnyx sends `message.received` webhook to the function
2. **receive()** → logs the message in `this.messages` (durable history), queues `process()` as a background task, acks the webhook in milliseconds
3. **process()** → reads history via `this.messages.toOpenAI()`, calls `this.env.TELNYX.ai.openai.chat.createCompletion()` (no API key), adds the reply to history, sends SMS via `this.env.TELNYX.messages.send()` (no API key), schedules a 24h follow-up
4. **followup()** → fires 24h later, checks if the customer replied (last message role), if not sends "Did that solve your problem?"
5. **Persistence** — conversation history, state, and the scheduled timer all survive restarts in the actor's durable storage

## Agent SDK Primitives Used

| Primitive | API | What it does |
|-----------|-----|--------------|
| Message History | `this.messages.add()` / `this.messages.toOpenAI()` / `this.messages.last()` | Durable conversation log per phone number |
| Scheduled Tasks | `this.queue("process")` / `this.schedule(86400, "followup")` | Background processing + 24h follow-up timer |
| Durable State | `this.setState()` / `this.getState()` | Per-conversation state (from, to, lastReply) |
| Telnyx Binding | `this.env.TELNYX.messages.send()` / `this.env.TELNYX.ai.openai.chat.createCompletion()` | Zero-credential SMS + inference |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `404 page not found` | Function still deploying | Wait ~30s, then retry |
| Actor not processing | `[telnyx]` binding missing | Ensure `telnyx.toml` has `[telnyx] binding = "TELNYX"` |
| No SMS reply | Messaging profile webhook not set | Point webhook to `/webhooks/sms` |
| LLM returns empty | Model unavailable | Check model name in `supportAgent.ts` |

## Related Examples

- [Edge URL Summarizer (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-url-summarizer/README.md)
- [Edge Agri Crop Advisory (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-agri-crop-advisory/README.md)
- [Edge Prompt A/B Tester (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-prompt-ab-tester/README.md)
- [AI Voicemail Smart Router (Python)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/voicemail-smart-router-python/README.md)

## Agent Discovery

This example is part of the [Telnyx Code Examples](https://github.com/team-telnyx/telnyx-code-examples) catalog.

- **Agent signup**: [telnyx.com/agent-signup.md](https://telnyx.com/agent-signup.md) — automated account provisioning via agent mail; get an API key with no human intervention
- **Agent CLI**: [github.com/team-telnyx/ai/tree/main/cli](https://github.com/team-telnyx/ai/tree/main/cli) — composite commands for agents ([commands reference](https://github.com/team-telnyx/ai/tree/main/cli/src/commands))
- **Agent skills**: [github.com/team-telnyx/ai/tree/main/skills](https://github.com/team-telnyx/ai/tree/main/skills)
- **Telnyx AI repo**: [github.com/team-telnyx/ai](https://github.com/team-telnyx/ai)
- **LLM-optimized docs**: [`llms-full.txt`](https://developers.telnyx.com/llms-full.txt)
- **Example index**: [`llms.txt`](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/llms.txt)
- **Telnyx CLI (human)**: [developers.telnyx.com/development/cli](https://developers.telnyx.com/development/cli) — `go install github.com/team-telnyx/telnyx-cli/cmd/telnyx@latest`

## Resources

- [Agent SDK Overview](https://developers.telnyx.com/docs/agent-sdk)
- [Agent SDK Quickstart](https://developers.telnyx.com/docs/agent-sdk/quickstart)
- [Roll Your Own Agent](https://developers.telnyx.com/docs/agent-sdk/examples/roll-your-own)
- [Stateful Actors Quick Start](https://developers.telnyx.com/docs/edge-compute/stateful-actors/quick-start)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Messaging Guide](https://developers.telnyx.com/docs/messaging)
- [Edge Compute CLI](https://github.com/team-telnyx/edge-compute/releases)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network.
