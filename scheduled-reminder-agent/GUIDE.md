# Build a Scheduled Reminder Agent

SMS reminder agent on Telnyx Edge Compute + Agent SDK — sends scheduled reminders via zero-credential SMS, detects snooze intent via LLM inference, and adapts timing with exponential backoff based on response patterns.

## How It Works

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
  └──────────────────────────────────────────────────┘
```

## Telnyx Products Used

- **Edge Compute (Agent SDK)** — `Agent` base class from `@telnyx/edge-runtime` with scheduled tasks and durable state
- **Messaging** — via `this.env.TELNYX.messages.send()` (pre-authenticated `[telnyx]` binding)
- **AI Inference** — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated `[telnyx]` binding) for snooze intent detection

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- A Telnyx phone number with a messaging profile (for real SMS)

## Step 1: Understand the Code

### `src/reminderAgent.ts` — The Agent

```typescript
export class ReminderAgent extends Agent<ReminderEnv, ReminderState> {
  async scheduleReminder(message, delaySeconds, fromNumber, phoneNumber) {
    const id = `reminder-${Date.now()}`;
    await this.schedule(delaySeconds, "sendReminder", { id }, { id: `send-${id}` });
    return id;
  }

  async sendReminder(data: { id: string }) {
    await this.env.TELNYX.messages.send({
      from: state.fromNumber,
      to: state.phoneNumber,
      text: `Reminder: ${reminder.message}\n\nReply "snooze" to delay...`,
    });
    await this.schedule(3600, "replyTimeout", { id: data.id });
  }

  async receiveReply(text: string) {
    const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
      model: "zai-org/GLM-5.2",
      messages: [
        { role: "system", content: SNOOZE_SYSTEM_PROMPT },
        { role: "user", content: `User reply: "${text}"` },
      ],
    });
    const { intent, delay_minutes } = JSON.parse(completion.choices[0].message.content);

    if (intent === "snooze") {
      const delay = adaptiveBaseSeconds * Math.pow(2, reminder.snoozeCount);
      await this.schedule(delay, "sendReminder", { id: reminder.id });
    } else {
      reminder.status = "done";
    }
  }
}
```

### `src/index.ts` — The Front Door

Routes inbound SMS webhooks and REST API calls to the per-phone-number actor:

```typescript
// Schedule a reminder
if (url.pathname === "/remind") {
  await env.REMINDER.idFromName(actorName(to)).scheduleReminder(message, delay, from, to);
}

// Inbound SMS reply
if (evt.event_type === "message.received") {
  await env.REMINDER.idFromName(actorName(from)).receiveReply(text);
}
```

### `telnyx.toml` — Config

```toml
[[actors]]
binding = "REMINDER"
type = "ReminderAgent"

[telnyx]
binding = "TELNYX"  # pre-authenticated client — no API key in code
```

### Agent SDK Primitives

| Primitive | Method | Purpose |
|-----------|--------|---------|
| Scheduled Tasks | `this.schedule(seconds, methodName, payload)` | Durable timers for reminder delivery and reply timeouts |
| Durable State | `this.setState()` / `this.getState()` | Per-phone-number state (reminders, snooze history, adaptive base) |
| Telnyx Binding | `this.env.TELNYX.messages.send()` | Zero-credential SMS |
| Telnyx Binding | `this.env.TELNYX.ai.openai.chat.createCompletion()` | Zero-credential snooze intent detection |

## Step 2: Deploy

```bash
npm install
telnyx-edge ship
```

## Step 3: Point your messaging profile webhook

In the [Telnyx Portal](https://portal.telnyx.com/messaging/profiles):
1. Create or edit a Messaging Profile assigned to your Telnyx number
2. Set the **Webhook URL** → `https://scheduled-reminder-agent-<id>.telnyxcompute.com/webhooks/sms`

## Step 4: Test

### Health

```bash
curl https://scheduled-reminder-agent-<id>.telnyxcompute.com/health/liveness
```

### Schedule a reminder (real SMS)

```bash
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/remind \
  -H "Content-Type: application/json" \
  -d '{"to":"+17177247292","message":"Time for your meeting","delay_minutes":5}'
```

### Simulate without real SMS

```bash
# Schedule a reminder with 6-second delay
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/remind \
  -H "Content-Type: application/json" \
  -d '{"to":"+17177247292","message":"Test reminder"}'

# Simulate a snooze reply
curl -X POST https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/reply \
  -H "Content-Type: application/json" \
  -d '{"from":"+17177247292","text":"snooze for 2 hours"}'

# Inspect state
curl "https://scheduled-reminder-agent-<id>.telnyxcompute.com/debug/state?from=+17177247292"
```

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

## Going to Production

- **Webhook signature verification** — verify the `telnyx-signature-ed25519` header before processing
- **Multiple reminders** — the actor handles multiple reminders per phone number; add a REST endpoint to list them
- **Timezone awareness** — schedule reminders in the user's timezone
- **Escalation** — if max snoozes reached, send a different message or escalate to a phone call
- **Analytics** — track snooze patterns to optimize the base delay
- **Multi-language** — detect language and adapt the snooze prompt

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/scheduled-reminder-agent/README.md)
- [Agent SDK Overview](https://developers.telnyx.com/docs/agent-sdk)
- [Agent SDK Quickstart](https://developers.telnyx.com/docs/agent-sdk/quickstart)
- [Roll Your Own Agent](https://developers.telnyx.com/docs/agent-sdk/examples/roll-your-own)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
