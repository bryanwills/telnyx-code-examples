---
name: conference-agent-mediator
title: "Conference Agent Mediator"
description: "An AI meeting facilitator that joins conference calls, transcribes, mediates turn-taking, and sends post-call summaries via SMS."
language: typescript
framework: edge
telnyx_products: ["Call Control", "Agent SDK", "Inference", "WebSocket"]
---

# Conference Agent Mediator

An AI meeting facilitator built on Telnyx Edge that joins conference calls, transcribes participants in real-time, mediates turn-taking via an LLM, and delivers post-conference summaries via SMS.

## Why Telnyx

Telnyx provides a unified AI Communications Infrastructure platform that bridges programmable voice (Call Control), real-time AI inference, and messaging. This sample demonstrates how to orchestrate these primitives on the Telnyx Edge runtime to build a stateful, conversational agent that actively participates in and manages conference calls without managing separate servers or webhooks.

## Telnyx API Endpoints Used

- **Call Control: Conferences** — Create a conference, join an agent, and manage audio legs.
- **Call Control: Speak** — Inject synthesized speech into the conference to prompt specific participants.
- **Call Control: Listen** — Stream real-time audio from the conference to the agent for transcription.
- **Agent SDK** — `class ConferenceAgent extends Agent` for maintaining conversation state and lifecycle.
- **Inference Binding** — Speech-to-Text (STT) transcription and Large Language Model (LLM) turn-tracking.
- **Programmable SMS** — Send the post-conference summary to specified observers.
- **WebSocket API** — Broadcast live transcripts to connected observer clients.

## Architecture

```text
+------------------+       +-------------------+       +-------------------+
|  PSTN / SIP      |       |  Telnyx Edge      |       |  Observer Client  |
|  Participants    |       |  (src/index.ts)   |       |  (WebSocket)      |
+--------+---------+       +---------+---------+       +---------+---------+
         |                           |                           |
         | (Join Conference)          |                           |
         v                           v                           |
+------------------+       +-------------------+                 |
| Call Control     |<=====>| ConferenceAgent    |                 |
| Conference       |       | (extends Agent)    |                 |
+------------------+       +---------+---------+                 |
         |                           |                           |
         | (Listen Audio)            |                           |
         v                           v                           |
+------------------+       +-------------------+                 |
| Inference (STT)  |======>| LLM Turn-Taking   |================>|
+------------------+       +---------+---------+                 |
         |                           |                           |
         |                           | (Speak Prompt)            |
         |                           v                           |
         |                   +-------------------+               |
         |                   | Call Control      |               |
         |                   | (Speak)           |               |
         |                   +-------------------+               |
         |                           |                           |
         | (Conference End)           |                           |
         v                           v                           |
+------------------+       +-------------------+                 |
| Inference (LLM)  |======>| Summary Generator |                 |
+------------------+       +---------+---------+                 |
         |                           |                           |
         |                           v                           |
         |                   +-------------------+               |
         |                   | Programmable SMS  |               |
         |                   +-------------------+               |
```

## Environment Variables

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `your_telnyx_api_key_here` | **yes** | TELNYX_API_KEY | — |

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/conference-agent-mediator

# 2. Create your environment file
cp .env.example .env

# 3. Edit .env and add your Telnyx API Key
# TELNYX_API_KEY=your_telnyx_api_key_here

# 4. Install dependencies
npm install

# 5. Run the local Edge development server
npm run dev
```

## API Reference

See `API.md` for the full typed endpoint reference, including route parameters, request/response shapes, and status codes for the Edge application.

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `TELNYX_API_KEY is missing` | Environment variable not set | Ensure `.env` exists and contains `TELNYX_API_KEY=...` |
| `Agent fails to join conference` | Invalid conference ID or Call Control setup | Verify the conference was created successfully via Call Control API before the agent attempts to join. |
| `No audio/transcription received` | Listen leg not established | Ensure the agent has an active `listen` command streaming audio to the inference binding. |
| `WebSocket observers disconnect` | Network interruption or timeout | Implement reconnection logic on the observer client side. |
| `SMS summary not received` | Invalid destination number or live mode disabled | Verify the target phone number format and ensure the app is configured for live mode if testing real SMS delivery. |

## Agent Discovery

- [Telnyx Agent Signup](https://telnyx.com/agent-signup.md)
- [Team Telnyx AI on GitHub](https://github.com/team-telnyx/ai)
- [llms.txt](https://telnyx.com/llms.txt)

## Related Examples

- `call-control-listen` — Basic audio streaming via Call Control.
- `agent-voice-bot` — Building a conversational voice agent using the Agent SDK.
- `websocket-transcription-relay` — Broadcasting STT streams to external clients.

## Resources

- [Telnyx Developer Docs](https://developers.telnyx.com/)
- [Call Control API Reference](https://developers.telnyx.com/docs/api/v2/call-control)
- [Telnyx Edge SDK](https://github.com/team-telnyx/edge-sdk)
- [Programmable SMS](https://developers.telnyx.com/docs/api/v2/messaging)
- [Telnyx Pricing](https://telnyx.com/pricing)
