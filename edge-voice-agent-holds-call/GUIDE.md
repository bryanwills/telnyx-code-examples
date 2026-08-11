# Build a Voice Agent That Holds a Call

Voice agent on Telnyx Edge Compute + Agent SDK — answers an inbound phone call and runs an STT → LLM → TTS conversation loop, all in the same PoP. Uses the `[telnyx]` binding for zero-credential inference and the `Agent` base class for durable call state and conversation history.

## How It Works

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

## Telnyx Products Used

- **Edge Compute (Agent SDK)** — `Agent` base class from `@telnyx/edge-runtime` with message history and durable state
- **Call Control** — answer, speak (TTS), transcription_start/stop (streaming STT), hangup
- **AI Inference** — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated `[telnyx]` binding)

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- A Telnyx phone number with a Call Control application

## Step 1: Understand the Code

### `src/voiceAgent.ts` — The Agent

```typescript
export class VoiceAgent extends Agent<VoiceEnv, CallState> {
  async recordStart(callControlId, from, to) {
    await this.setState({ callControlId, from, to, phase: "answering" });
  }

  async appendUser(text: string) {
    await this.messages.add("user", text);  // durable history
  }

  async respond(): Promise<string> {
    const history = await this.messages.toOpenAI();
    const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
      model: "zai-org/GLM-5.2",
      messages: [{ role: "system", content: SYSTEM_PROMPT }, ...history],
    });
    const reply = completion.choices[0].message.content;
    await this.messages.add("assistant", reply);
    return reply;  // webhook handler speaks this via Call Control
  }

  async finishCall() {
    await this.setState({ phase: "done", endedAt: Date.now() });
  }
}
```

### `src/index.ts` — The Webhook Router

Drives the call loop by dispatching Call Control webhook events to the per-call actor:

```typescript
if (eventType === "call.initiated") {
  await stub.recordStart(callControlId, from, to);
  await answerCall(apiKey, callControlId);
}

if (eventType === "call.answered") {
  await stub.setPhase("greeting");
  await speakText(apiKey, callControlId, GREETING, "greeting");
}

if (eventType === "call.speak.ended") {
  await stub.setPhase("listening");
  await startTranscription(apiKey, callControlId);  // STT
}

if (eventType === "call.transcription" && isFinal) {
  await stub.appendUser(transcript);
  await stopTranscription(apiKey, callControlId);
  const reply = await stub.respond();  // LLM via zero-credential binding
  await speakText(apiKey, callControlId, reply, "reply");  // TTS — loop
}

if (eventType === "call.hangup") {
  await stub.finishCall();  // state persisted
}
```

### `telnyx.toml` — Config

```toml
[[actors]]
binding = "VOICE_AGENT"
type = "VoiceAgent"

[telnyx]
binding = "TELNYX"  # pre-authenticated client — no API key in code for inference

[[secrets]]
binding = "TELNYX_API_KEY"
name = "TELNYX_API_KEY"  # used for Call Control REST (answer, speak, transcription)

[env_vars]
AI_MODEL = "zai-org/GLM-5.2"
```

### Agent SDK Primitives

| Primitive | Method | Purpose |
|-----------|--------|---------|
| Message History | `this.messages.add()` / `.toOpenAI()` / `.last()` | Durable conversation log per call |
| Durable State | `this.setState()` / `this.getState()` | Per-call state (callId, from, to, phase, turnCount) |
| Telnyx Binding | `this.env.TELNYX.ai.openai.chat.createCompletion()` | Zero-credential AI inference |

### Why Streaming Transcription Instead of `gather(using=speech)`

The Call Control `gather` action captures DTMF digits, not speech-to-text. The `gather_using_ai` action runs Telnyx's hosted AI assistant with its own conversation loop — but this example uses our own LLM via the zero-credential `[telnyx]` binding. So we use **streaming transcription** (`transcription_start` with the Google engine on the inbound track) for STT, which delivers the caller's speech as text that we feed into our own LLM. This keeps the full conversation loop — STT, inference, TTS — in our code on Edge Compute.

## Step 2: Deploy

```bash
npm install
telnyx-edge ship
```

## Step 3: Point your Call Control webhook

In the [Telnyx Portal](https://portal.telnyx.com):
1. Create or edit a Call Control application assigned to your Telnyx number
2. Set the **Webhook URL** → `https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/webhooks/voice`

## Step 4: Test

### Health

```bash
curl https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/health/liveness
```

### Real call (requires Call Control application)

1. Call your Telnyx number from your phone
2. The agent answers, speaks the greeting, and listens
3. Speak — the agent transcribes, runs the LLM, and speaks back
4. The loop continues until you hang up

### Inspect call state

```bash
curl "https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/debug/call?call_control_id=<your_call_id>"
```

## Going to Production

- **Webhook signature verification** — verify the `telnyx-signature-ed25519` header before processing
- **Barge-in** — detect interim transcripts and stop TTS when the caller interrupts
- **Conversation limits** — cap turn count or call duration in the actor
- **Multi-language** — detect language and route to a language-specific system prompt
- **Human handoff** — add a tool that transfers to a human when the LLM can't answer
- **Voice selection** — try different TTS voices (`Telnyx.KokoroTTS.af`, `female`, `male`)
- **Cost tracking** — track tokens used per call in state

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-voice-agent-holds-call/README.md)
- [Agent SDK Overview](https://developers.telnyx.com/docs/agent-sdk)
- [Agent SDK Quickstart](https://developers.telnyx.com/docs/agent-sdk/quickstart)
- [Roll Your Own Agent](https://developers.telnyx.com/docs/agent-sdk/examples/roll-your-own)
- [Call Control API Reference](https://developers.telnyx.com/api-reference/call-control)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
