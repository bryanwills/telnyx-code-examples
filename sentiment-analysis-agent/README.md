---
name: sentiment-analysis-agent
title: "Sentiment Analysis Agent"
description: "Analyze inbound SMS sentiment on Telnyx Edge Compute with the Agent SDK, log results to actor-local SQL, and escalate negative sentiment by SMS."
language: nodejs
framework: telnyx-edge
telnyx_products: [Edge Compute, Messaging, AI]
channel: [sms]
---

# Sentiment Analysis Agent

Analyze inbound SMS sentiment in real time with a Telnyx Edge Compute agent. Each inbound message is classified by Telnyx Inference, logged to actor-local SQL, and negative sentiment triggers an SMS escalation to a human ops number.

The sample includes a browser simulator so you can demo the full agent loop while toll-free or 10DLC messaging compliance is still pending. In demo mode, only the carrier SMS transport is replaced; the Edge function, Agent SDK, Inference call, SQL log, and escalation decision all remain real.

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform for voice, messaging, SIP, AI, and IoT on one private global network. This sample keeps sentiment classification, durable state, and escalation logic on Telnyx Edge Compute, close to the inbound message path, while using the `[telnyx]` binding for zero-credential AI inference and SMS sends.

## Telnyx APIs Used

- **Edge Compute**: deploys the HTTP handler and `SentimentAgent` actor.
- **Agent SDK**: `class SentimentAgent extends Agent`.
- **Telnyx Inference binding**: `this.env.TELNYX.ai.openai.chat.createCompletion()`.
- **Telnyx Messaging binding**: `this.env.TELNYX.messages.send()`.
- **Actor-local SQL**: `this.ctx.storage.sql`.
- **Messaging webhooks**: `message.received`.

## Architecture

```
Inbound SMS webhook
      |
      v
Edge fetch handler
      |
      v
SentimentAgent.receive()
  - dedup webhook event id
  - append message history
  - queue process()
      |
      v
SentimentAgent.process()
  - classify sentiment with Telnyx Inference
  - write SQL row
  - if negative, send ops SMS in production
  - auto-reply to sender in production
```

In demo mode:

```
Browser /send -> same SentimentAgent -> real Inference -> real SQL -> /events UI
```

## Prerequisites

- Telnyx account with Edge Compute enabled
- `telnyx-edge` CLI v0.2.5 or newer
- Node.js 20+
- A Telnyx API key for `telnyx-edge auth api-key set`
- For production SMS: a messaging-capable Telnyx number assigned to a messaging profile, plus toll-free verification or 10DLC approval as required

## Setup

```bash
cd telnyx-code-examples/sentiment-analysis-agent
npm install
npm run typecheck
npm run types
```

Authenticate the Edge CLI:

```bash
telnyx-edge auth api-key set "$TELNYX_API_KEY"
telnyx-edge auth status
```

For a fresh deployable function, scaffold with the CLI so Telnyx assigns a function id:

```bash
telnyx-edge new-func --actor --name=sentiment-analysis-agent
```

Then copy this sample's `src/`, docs, dependencies, and binding blocks into the generated project. Keep the generated `[edge_compute]` `func_id` if the CLI adds one.

## Configuration

`telnyx.toml` defaults to demo mode. The code only switches into real SMS mode when `PRODUCTION_MODE = "true"`, so first deploys do not accidentally attempt carrier SMS:

```toml
[env_vars]
DEMO_MODE = "true"
PRODUCTION_MODE = "false"
DEMO_FROM_NUMBER = "+15557654321"
DEMO_SENDER_NUMBER = "+15551234567"
OPS_ALERT_PHONE = "+15559876543"
MODEL = "zai-org/GLM-5.2"
```

For production webhooks, add the Telnyx public key as a secret:

```bash
telnyx-edge secrets add TELNYX_PUBLIC_KEY "<base64 public key from Mission Control>"
```

## Demo Mode

Ship the function:

```bash
telnyx-edge ship
```

Open the deployed function URL in a browser. The page lets you simulate inbound SMS messages and shows the live sentiment log.

Try:

- `I love this app, just paid for a year`
- `What are your hours?`
- `this is broken and nobody is helping me, I want a refund`

Negative rows show a **Human escalation triggered** badge. In production, the same branch sends an SMS to `OPS_ALERT_PHONE`.

## Production SMS

To switch to real SMS:

1. Set `PRODUCTION_MODE = "true"` in `telnyx.toml`.
2. Store `TELNYX_PUBLIC_KEY` with `telnyx-edge secrets add`.
3. Ship the function.
4. Set your messaging profile webhook URL to `https://<your-function>.telnyxcompute.com/webhooks/messaging`.
5. Confirm the number is approved for off-net US messaging: toll-free verification for toll-free numbers, or 10DLC brand/campaign/number assignment for US long codes.

Carrier compliance cannot be bypassed in code. If verification is pending, keep `PRODUCTION_MODE = "false"` for filming or use Telnyx-to-Telnyx on-net messaging for a real transport smoke test.

## Endpoints

| Method | Path | Mode | Purpose |
| --- | --- | --- | --- |
| `GET` | `/` | demo | Browser simulator |
| `POST` | `/send` | demo | Simulate inbound SMS |
| `GET` | `/events?from=+15551234567` | demo | Read actor SQL sentiment log |
| `POST` | `/reset` | demo | Clear the demo sentiment log for one sender |
| `POST` | `/webhooks/messaging` | production | Telnyx Messaging webhook |
| `GET` | `/health` | both | Health check |

## SQL Schema

```sql
CREATE TABLE sentiment(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sender TEXT NOT NULL,
  message TEXT NOT NULL,
  label TEXT NOT NULL,
  score REAL NOT NULL,
  escalated INTEGER NOT NULL,
  reply TEXT NOT NULL,
  at INTEGER NOT NULL
);
```

## Troubleshooting

| Issue | Cause | Fix |
| --- | --- | --- |
| Browser shows no events | LLM work is queued and may still be running | Wait a few seconds or click Refresh |
| Production webhook returns 401 | Missing or invalid `TELNYX_PUBLIC_KEY` | Add the secret and verify webhook signatures use API v2 |
| Inbound SMS does not arrive | Messaging profile webhook URL is not set | Point the profile to `/webhooks/messaging` |
| SMS sends are blocked | Toll-free verification or 10DLC is incomplete | Use demo mode or on-net testing until approval |
| Duplicate webhook attempts create one row | Expected behavior | `webhook_events(event_id PRIMARY KEY)` dedups retries |

## Related Examples

- [send-sms-nodejs](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/send-sms-nodejs/README.md)
- [receive-sms-webhook-nodejs](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/receive-sms-webhook-nodejs/README.md)
- [run-llm-inference-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/run-llm-inference-python/README.md)

## Agent Discovery

- [Telnyx Agent Signup](https://telnyx.com/products/voice-ai-agents)
- [Agent CLI](https://github.com/team-telnyx/ai)
- [Telnyx CLI](https://github.com/team-telnyx/telnyx-cli)
- [llms-full.txt](https://developers.telnyx.com/llms-full.txt)
- [llms.txt](https://developers.telnyx.com/llms.txt)

## Resources

- [Telnyx Edge Compute](https://developers.telnyx.com/docs/edge-compute)
- [Messaging Webhooks](https://developers.telnyx.com/docs/messaging/messages/receiving-webhooks)
- [Messaging Profiles](https://developers.telnyx.com/docs/messaging/messages/messaging-profiles-overview)
- [Send Messages](https://developers.telnyx.com/docs/messaging/messages/send-message)
