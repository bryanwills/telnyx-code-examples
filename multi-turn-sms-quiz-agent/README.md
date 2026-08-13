---
name: multi-turn-sms-quiz-agent
title: "Multi-Turn SMS Quiz Agent"
description: "Adaptive SMS quiz agent on Telnyx Edge Compute with durable per-sender state, LLM-generated questions, SQL event history, and browser demo mode."
language: nodejs
framework: telnyx-edge
telnyx_products: [Edge Compute, Messaging, AI]
channel: [sms]
---

# Multi-Turn SMS Quiz Agent

An adaptive SMS quiz agent on Telnyx Edge Compute. Each sender gets a durable
`QuizAgent` StatefulActor that tracks score, difficulty, current question, and
quiz history across turns.

The default mode works around messaging compliance delays by replacing only the
carrier SMS transport with a browser simulator. Edge Compute, the Agent SDK,
StatefulActor state, SQL, and Telnyx Inference still run live.

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform for voice, messaging, SIP, AI, and IoT on one private global network. This sample combines durable Edge Compute actors, zero-credential Telnyx Inference, and Messaging so every participant gets a stateful quiz session without a separate app server.

## What it uses

- `QuizAgent extends Agent` from `@telnyx/edge-runtime`
- `[telnyx]` binding for zero-credential Telnyx Inference and Messaging
- `this.setState()` for durable quiz state
- actor-local SQL for quiz events and webhook idempotency
- `this.queue("process")` so webhooks ack quickly and LLM work runs async

## Run

```bash
npm install
npm run typecheck
npm run types
npm run ship
```

Open the deployed function URL in a browser. In demo mode, type `start`, then
reply with `a`, `b`, or `c`. The live panel shows phase, score, difficulty, and
turn while `/events` reads the actor SQL log.

## Demo vs production SMS

The browser simulator is controlled by `DEMO_MODE`; it is available unless
`DEMO_MODE = "false"` is set.
Real SMS transport is controlled by `SMS_TRANSPORT`; any value other than
`"demo"` enables signed webhooks and outbound `messages.send()`.

In demo mode:

- `POST /send` simulates inbound SMS.
- `GET /events` and `GET /status` power the browser UI.
- No outbound SMS is sent, so carrier compliance does not block the demo.

For production SMS:

1. Set `SMS_TRANSPORT = "production"`.
2. Store the Telnyx webhook public key:

   ```bash
   telnyx-edge secrets add TELNYX_PUBLIC_KEY "<public key>"
   ```

3. Point the messaging profile webhook to:

   ```text
   https://<function-url>/webhooks/messaging
   ```

4. Use an SMS-capable number with approved 10DLC/toll-free compliance.

When SMS transport is enabled, the same actor sends quiz questions, grades,
and final scores through `this.env.TELNYX.messages.send()`.

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| Browser simulator is not visible | `DEMO_MODE` is set to `"false"` | Set `DEMO_MODE = "true"` and ship again |
| Quiz responses do not appear immediately | LLM work runs asynchronously in the actor queue | Wait a few seconds or refresh the demo panel |
| Production webhooks return 401 | Missing or invalid `TELNYX_PUBLIC_KEY` | Add the Telnyx public key as an Edge secret |
| Outbound SMS does not send | Messaging compliance or profile setup is incomplete | Keep `SMS_TRANSPORT = "demo"` until the number and profile are approved |

## Related Examples

- [agent-sms-triage-bot](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/agent-sms-triage-bot/README.md)
- [sms-support-agent-with-followup](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sms-support-agent-with-followup/README.md)
- [edge-prompt-ab-tester](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-prompt-ab-tester/README.md)

## Agent Discovery

- [Telnyx Agent Signup](https://telnyx.com/products/voice-ai-agents)
- [Agent CLI](https://github.com/team-telnyx/ai)
- [Telnyx CLI](https://github.com/team-telnyx/telnyx-cli)
- [llms-full.txt](https://developers.telnyx.com/llms-full.txt)
- [llms.txt](https://developers.telnyx.com/llms.txt)
