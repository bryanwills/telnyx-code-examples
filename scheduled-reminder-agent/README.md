---
name: scheduled-reminder-agent
title: "Scheduled Reminder Agent"
description: "SMS reminder agent on Telnyx Edge Compute + Agent SDK — sends scheduled reminders via zero-credential SMS, detects snooze intent via LLM, and adapts timing with exponential backoff."
language: nodejs
framework: telnyx-edge (Agent SDK)
telnyx_products: [Edge Compute, Messaging, AI Inference]
---

# Scheduled Reminder Agent

SMS reminder agent on Telnyx Edge Compute + Agent SDK — sends scheduled reminders via zero-credential SMS, detects snooze intent via LLM inference, and adapts timing based on response patterns using exponential backoff. Uses the `[telnyx]` binding for zero-credential SMS and inference — no API key anywhere in code.

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network. This example composes scheduled tasks, durable state, zero-credential messaging, and LLM inference on Edge Compute in a single deployable function — an adaptive reminder agent that learns from user responses.

## Telnyx API Endpoints Used

- **Messaging**: `POST /v2/messages` — via `this.env.TELNYX.messages.send()` (pre-authenticated binding, zero-credential)
- **AI Inference**: `POST /v2/ai/openai/chat/completions` — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated binding, zero-credential) for snooze intent detection

## Architecture

```
  POST /remind → ReminderAgent.scheduleReminder(message, delay)
        │
        ▼
  ┌──────────────────────────────────────────────────┐
  │ Agent SDK (Stateful Actor)                        │
  │                                                  │
  │  1. this.schedule(delay, "sendReminder")         │
  │  2. sendReminder():                              │
  │     → env.TELNYX.messages.send()  (SMS sent)     │
  │     → this.schedule(1h, "replyTimeout")          │
  │  3. User replies via SMS webhook:                │
  │     → receiveReply(text)                          │
  │     → env.TELNYX.ai.openai.chat                  │
  │       .createCompletion()  (snooze detection)    │
  │     → if snooze:                                  │
  │         → adaptive delay = base × 2^snoozeCount  │
  │         → this.schedule(delay, "sendReminder")   │
  │     → if acknowledge:                             │
  │         → mark done                               │
  │  4. Adaptive timing:                               │
  │     → 30min → 1h → 2h → 4h → 8h (max 5 snoozes)  │
  └──────────────────────────────────────────────────┘
```

## Environment Variables / Secrets

No API key needed in code — the `[telnyx]` binding in `telnyx.toml` carries auth for both messaging and inference.

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `[telnyx]` binding | toml | **yes** | Pre-authenticated Telnyx client (messaging + inference) |
| `AI_MODEL` | env_var | no | Inference model name (default: `zai-org/GLM-5.2`) |

> **Agent / CLI access**
>
> ```bash
> # Buy a phone number for sending reminders
> telnyx number-orders create --phone-number "+16282564655"
>
> # List your numbers
> telnyx numbers list
> ```

## Setup

### Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- A Telnyx phone number with a messaging profile (for real SMS)

### 1. Clone and install

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/scheduled-reminder-agent
npm install
```

### 2. Deploy

```bash
telnyx-edge ship
```

`ship` prints a URL like `scheduled-reminder-agent-<id>.telnyxcompute.com`.

<details><summary>Programmatic / CLI setup</summary>

```bash
# Buy a number (if you don't have one)
telnyx number-orders create --phone-number "+16282564655"

# Create a messaging profile
telnyx messaging-profiles create --name "reminder-agent"

# Assign the number to the messaging profile
telnyx numbers update +16282564655 --messaging-profile-id <profile_id>
```

</details>

### 3. Point your messaging profile webhook

In the [Telnyx Portal](https://portal.telnyx.com/messaging/profiles):
1. Create or edit a Messaging Profile assigned to your Telnyx number
2. Set the **Webhook URL** → `https://scheduled-reminder-agent-<id>.telnyxcompute.com/webhooks/sms`

### 4. Test

```bash
# Health check
curl https://scheduled-reminder-agent-<id>.telnyxcompute.com/health/liveness

# Schedule a reminder (sends SMS after delay_minutes)
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/remind \
  -H "Content-Type: application/json" \
  -d '{"to":"+17177247292","message":"Time to take your medication","delay_minutes":5}'

# Simulate a snooze reply (no real SMS needed)
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/reply \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","text":"snooze for an hour"}'

# Inspect actor state
curl "https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/state?from=+17177247292"
```

## API Reference

See [API.md](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/scheduled-reminder-agent/API.md) for the full typed endpoint reference.

## How It Works

1. **Schedule** — `POST /remind` creates a `ReminderAgent` actor keyed by the recipient's phone number and calls `scheduleReminder()`, which uses `this.schedule()` to queue `sendReminder()` after the specified delay
2. **Send** — when the timer fires, `sendReminder()` sends an SMS via `this.env.TELNYX.messages.send()` (zero-credential) and starts a 1-hour reply window
3. **Reply** — when the user replies via SMS, the webhook routes to `receiveReply()`, which calls `this.env.TELNYX.ai.openai.chat.createCompletion()` to detect snooze vs. acknowledge intent
4. **Snooze** — if the LLM detects snooze intent, the reminder is rescheduled with an adaptive delay (exponential backoff: 30min → 1h → 2h → 4h → 8h, max 5 snoozes)
5. **Acknowledge** — if the user acknowledges or the reply window expires, the reminder is marked done
6. **Persistence** — all reminder state, response history, and scheduled timers survive restarts in the actor's durable storage

## Agent SDK Primitives Used

| Primitive | API | What it does |
|-----------|-----|--------------|
| Scheduled Tasks | `this.schedule(seconds, methodName, payload)` | Fire `sendReminder()` after a delay — durable, survives restarts |
| Durable State | `this.setState()` / `this.getState()` | Per-phone-number state (reminders, snooze count, adaptive base) |
| Message History | `this.messages.add()` / `this.messages.toOpenAI()` | Not used (SMS-based, not conversation-based) |
| Telnyx Binding | `this.env.TELNYX.messages.send()` | Zero-credential SMS |
| Telnyx Binding | `this.env.TELNYX.ai.openai.chat.createCompletion()` | Zero-credential snooze intent detection |

## Adaptive Timing

The agent uses exponential backoff for snoozed reminders:

| Snooze # | Delay (default base = 30 min) |
|----------|-------------------------------|
| 1st | 30 min |
| 2nd | 1 hour |
| 3rd | 2 hours |
| 4th | 4 hours |
| 5th | 8 hours |
| 6th+ | Reminder marked done (max snoozes reached) |

If the user specifies a time in their reply (e.g., "snooze for 2 hours"), the LLM extracts the delay and overrides the exponential backoff.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `404 page not found` | Function still deploying | Wait ~30s, then retry |
| No SMS sent | Messaging profile webhook not set | Point webhook to `/webhooks/sms` |
| Snooze not detected | LLM unavailable or misclassified | Check `AI_MODEL` env var — try `zai-org/GLM-5.2` |
| Reminder never fires | `this.schedule()` failed | Ensure `telnyx.toml` has `[[actors]]` with correct binding |
| Actor not processing | `[telnyx]` binding missing | Ensure `telnyx.toml` has `[telnyx] binding = "TELNYX"` |

## Related Examples

- [SMS Support Agent with Follow-Up (TypeScript, Agent SDK)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sms-support-agent-with-followup/README.md)
- [Edge Voice Agent That Holds a Call (TypeScript, Agent SDK)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-voice-agent-holds-call/README.md)
- [Edge URL Summarizer (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-url-summarizer/README.md)
- [Edge Prompt A/B Tester (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-prompt-ab-tester/README.md)

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
