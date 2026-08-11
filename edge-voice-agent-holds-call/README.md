---
name: edge-voice-agent-holds-call
title: "Edge Voice Agent That Holds a Call"
description: "Voice agent on Telnyx Edge Compute + Agent SDK — answers an inbound call and runs an STT → LLM → TTS conversation loop, all in the same PoP. Zero-credential inference via the [telnyx] binding."
language: nodejs
framework: telnyx-edge (Agent SDK)
telnyx_products: [Edge Compute, Voice, AI Inference]
---

# Edge Voice Agent That Holds a Call

Voice agent on Telnyx Edge Compute + Agent SDK — answers an inbound phone call and holds a conversation loop with streaming speech-to-text, LLM inference, and text-to-speech, all in the same PoP. Uses the `[telnyx]` binding for zero-credential inference — no API key in code for the LLM.

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI, and IoT on one private, global network. This example composes Call Control, streaming transcription, text-to-speech, AI inference, and stateful actors on Edge Compute in a single deployable function — the flagship "voice agent that holds a call" that only Telnyx can ship because we own the telephony network.

## Telnyx API Endpoints Used

- **Call Control**: `POST /v2/calls/{call_control_id}/actions/answer` — answer the inbound call
- **Call Control TTS**: `POST /v2/calls/{call_control_id}/actions/speak` — text-to-speech for greeting and replies
- **Call Control Transcription**: `POST /v2/calls/{call_control_id}/actions/transcription_start` — streaming STT (Google engine, inbound track)
- **Call Control Transcription**: `POST /v2/calls/{call_control_id}/actions/transcription_stop` — stop STT before LLM turn
- **Call Control Hangup**: `POST /v2/calls/{call_control_id}/actions/hangup` — end the call
- **AI Inference**: `POST /v2/ai/openai/chat/completions` — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated binding, zero-credential)

## Architecture

```
  Inbound call → webhook → VoiceAgent actor (one per call)
        │
        ▼
  ┌────────────────────────────────────────────────────┐
  │ call.initiated   → answer()                        │
  │ call.answered    → speak(greeting)                 │
  │ speak.ended      → transcription_start()           │
  │ call.transcription (final)                         │
  │   → appendUser(transcript)                         │
  │   → stopTranscription()                             │
  │   → respond()  ────────────────────────────┐        │
  │     │                                      │        │
  │     ▼  Agent SDK (Stateful Actor)          │        │
  │     ┌────────────────────────────────┐     │        │
  │     │ this.messages.toOpenAI()       │     │        │
  │     │ env.TELNYX.ai.openai.chat      │     │        │
  │     │   .createCompletion()          │     │        │
  │     │ this.messages.add("assistant") │     │        │
  │     └────────────────────────────────┘     │        │
  │   → speak(reply) ◄────────────────────────┘        │
  │ speak.ended      → transcription_start()  (loop)   │
  │ call.hangup      → finishCall() (state persisted)  │
  └────────────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `TELNYX_API_KEY` | secret | **yes** | Telnyx API key for Call Control REST (answer, speak, transcription, hangup) |
| `[telnyx]` binding | toml | **yes** | Pre-authenticated Telnyx client for zero-credential AI inference |
| `AI_MODEL` | env_var | no | Inference model name (default: `zai-org/GLM-5.2`) |

> **Agent / CLI access**
>
> ```bash
> # Buy a phone number for the voice agent
> telnyx number-orders create --phone-number "+16282564655"
>
> # List your numbers
> telnyx numbers list
> ```

## Setup

### Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- A Telnyx phone number with a Call Control application

### 1. Clone and install

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/edge-voice-agent-holds-call
npm install
```

### 2. Configure secrets

```bash
# Set your Telnyx API key as a secret on the Edge Compute function
telnyx-edge secret set TELNYX_API_KEY your_telnyx_api_key
```

<details><summary>Programmatic / CLI setup</summary>

```bash
# Buy a number (if you don't have one)
telnyx number-orders create --phone-number "+16282564655"

# Create a Call Control application
telnyx call-control-applications create \
  --application-name "voice-agent-holds-call" \
  --webhook-url "https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/webhooks/voice"

# Assign the number to the application
telnyx numbers update +16282564655 --connection-id <call_control_app_id>
```

</details>

### 3. Deploy

```bash
telnyx-edge ship
```

`ship` prints a URL like `edge-voice-agent-holds-call-<id>.telnyxcompute.com`.

### 4. Point your Call Control webhook

In the [Telnyx Portal](https://portal.telnyx.com):
1. Create or edit a Call Control application assigned to your Telnyx number
2. Set the **Webhook URL** → `https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/webhooks/voice`

### 5. Test

```bash
# Health check
curl https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/health/liveness

# Call your Telnyx number from your phone — the agent answers, greets, and converses
```

## API Reference

See [API.md](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-voice-agent-holds-call/API.md) for the full typed endpoint reference.

### `POST /webhooks/voice`

Receives Telnyx Call Control webhooks and drives the conversation loop. Events handled:

| Event | Action |
|-------|--------|
| `call.initiated` | Record start, answer the call |
| `call.answered` | Speak greeting |
| `call.speak.ended` (greeting/reply) | Start streaming transcription |
| `call.transcription` (final) | Stop transcription, run LLM turn, speak reply |
| `call.hangup` | Finalize call state |

### `GET /debug/call?call_control_id=...`

Inspect actor state for a call (phase, turn count, conversation history count, last message).

```bash
curl "https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/debug/call?call_control_id=v3:abc123"
```

### `POST /debug/respond`

Run an LLM turn without a live call (for testing the inference binding).

```bash
curl -X POST https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/debug/respond \
  -H "Content-Type: application/json" \
  -d '{"call_control_id":"v3:abc123"}'
```

### `GET /health/{liveness,readiness}`

Health checks.

## How It Works

1. **Inbound call** → Telnyx sends `call.initiated` webhook → the webhook handler creates a `VoiceAgent` actor keyed by `call_control_id` and calls `answer()`
2. **Greeting** → on `call.answered`, the handler speaks a greeting via Call Control TTS (`speak`)
3. **Listening** → when the greeting finishes (`call.speak.ended`), the handler starts streaming transcription (`transcription_start`, Google engine, inbound track only)
4. **Thinking** → when a final transcript arrives (`call.transcription` with `is_final=true`), the handler stops transcription, adds the user's speech to the actor's durable message history, and calls `respond()` on the actor
5. **Responding** → `respond()` reads conversation history via `this.messages.toOpenAI()`, calls `this.env.TELNYX.ai.openai.chat.createCompletion()` (zero-credential binding), adds the reply to history, and returns it for TTS
6. **Looping** → the reply is spoken via `speak()`; when it finishes, transcription starts again — the loop continues until the caller hangs up
7. **Persistence** — conversation history and call state (phase, turn count, timestamps) survive restarts in the actor's durable storage

## Agent SDK Primitives Used

| Primitive | API | What it does |
|-----------|-----|--------------|
| Message History | `this.messages.add()` / `this.messages.toOpenAI()` / `this.messages.last()` | Durable conversation log per call |
| Durable State | `this.setState()` / `this.getState()` | Per-call state (callId, from, to, phase, turnCount) |
| Telnyx Binding | `this.env.TELNYX.ai.openai.chat.createCompletion()` | Zero-credential AI inference |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Call answers but no audio | TTS voice unavailable | Check `TTS_VOICE` in `src/index.ts` — try `female` as fallback |
| No transcription events | Wrong transcription track | Ensure `transcription_tracks: "inbound"` — caller audio only |
| LLM returns empty | Model unavailable | Check `AI_MODEL` env var — try `zai-org/GLM-5.2` |
| `404 page not found` | Function still deploying | Wait ~30s, then retry |
| Actor not processing | `[telnyx]` binding missing | Ensure `telnyx.toml` has `[telnyx] binding = "TELNYX"` |
| `TELNYX_API_KEY not configured` | Secret not set | Run `telnyx-edge secret set TELNYX_API_KEY <key>` |

## Related Examples

- [SMS Support Agent with Follow-Up (TypeScript, Agent SDK)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/sms-support-agent-with-followup/README.md)
- [Edge URL Summarizer (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-url-summarizer/README.md)
- [Edge Prompt A/B Tester (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-prompt-ab-tester/README.md)
- [Edge Agri Crop Advisory (TypeScript)](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-agri-crop-advisory/README.md)

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
- [Call Control API Reference](https://developers.telnyx.com/api-reference/call-control)
- [Streaming Transcription Guide](https://developers.telnyx.com/docs/voice/programmable-voice/transcription)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Edge Compute CLI](https://github.com/team-telnyx/edge-compute/releases)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
