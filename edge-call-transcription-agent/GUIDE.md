# Build a Live Call Transcription Agent

Live call transcription agent on Telnyx Edge Compute + Agent SDK — answers an inbound call, streams speech-to-text into a durable per-call actor, and on hangup runs a non-blocking pipeline that summarizes the transcript via LLM, persists it to actor-local SQL, and texts the summary to a recipient via SMS. Uses the `[telnyx]` binding for zero-credential inference and messaging.

## How It Works

```
   Inbound call → webhook → TranscribeAgent actor (one per call_control_id)
         │
         ▼
   ┌────────────────────────────────────────────────────────────┐
   │ call.initiated       → recordStart()  + answer()           │
   │ call.answered        → speak(greeting)                     │
   │ call.speak.ended     → transcription_start()                │
   │ call.transcription (interim)                               │
   │   → appendTranscript(text, is_final=false)                 │
   │ call.transcription (final)                                 │
   │   → appendTranscript(text, is_final=true)                   │
   │     (state.transcriptText accumulates caller's final STT)   │
   │ call.hangup          → onHangup() → queue("summarize")     │
   └────────────────────────────────────────────────────────────┘
         │
         ▼   non-blocking pipeline (durable across restarts)
   ┌────────────────────────────────────────────────────────────┐
   │ summarize()                                                 │
   │   → this.env.TELNYX.ai.openai.chat.createCompletion()       │
   │ store()                                                     │
   │   → this.ctx.storage.sql (per-call row)                     │
   │   → TranscriptRegistry actor ("global") — cross-call index  │
   │ notify()                                                    │
   │   → this.env.TELNYX.messages.send({ from, to, text })       │
   └────────────────────────────────────────────────────────────┘
```

## Telnyx Products Used

- **Edge Compute (Agent SDK)** — `Agent` base class from `@telnyx/edge-runtime` with durable state, queue-based pipeline stages, and actor-local SQL
- **Call Control** — answer, speak (TTS), transcription_start/stop (streaming STT)
- **AI Inference** — via `this.env.TELNYX.ai.openai.chat.createCompletion()` (pre-authenticated `[telnyx]` binding)
- **Messaging** — via `this.env.TELNYX.messages.send()` (pre-authenticated `[telnyx]` binding)

## Prerequisites

- [Telnyx Edge CLI](https://github.com/team-telnyx/edge-compute/releases) v0.2.2+
- Node.js 18+
- A Telnyx phone number with a Call Control application
- A Telnyx number with SMS capability + 10DLC campaign attached (for the SMS summary)

## Step 1: Understand the Code

### `src/transcribeAgent.ts` — The Agent

Two actors in this file: `TranscribeAgent` (one per call) and `TranscriptRegistry` (a single shared "global" instance).

```typescript
export class TranscribeAgent extends Agent<TranscribeEnv, TranscribeState> {
  protected override initialState(): TranscribeState {
    return { callControlId: "", from: "", to: "", phase: "init", segments: [],
             transcriptText: "", summary: "", startedAt: 0, endedAt: 0,
             turnCount: 0, error: "" };
  }

  async recordStart(callControlId, from, to) {
    this.ensureTables();
    await this.setState({ callControlId, from, to, phase: "answering", startedAt: Date.now(), ... });
    this.ctx.storage.sql.exec(
      `INSERT OR REPLACE INTO transcript (call_control_id, from_number, to_number, ...) VALUES (?, ?, ...)`,
      callControlId, from, to, ...
    );
  }

  async appendTranscript(text, isFinal) {
    const state = await this.getState();
    const segments = [...state.segments, { text, at: Date.now(), isFinal }];
    const transcriptText = isFinal ? (state.transcriptText + " " + text).trim() : state.transcriptText;
    await this.setState({ ...state, segments, transcriptText, turnCount: state.turnCount + (isFinal ? 1 : 0) });
  }

  async onHangup() {
    await this.setState({ ...(await this.getState()), phase: "summarizing", endedAt: Date.now() });
    await this.queue("summarize");
  }

  async summarize() {
    const completion = await this.env.TELNYX.ai.openai.chat.createCompletion({
      model: "zai-org/GLM-5.2",
      messages: [{ role: "system", content: SUMMARY_SYSTEM_PROMPT },
                 { role: "user", content: state.transcriptText }],
    });
    await this.setState({ ...state, summary: completion.choices[0].message.content });
    await this.queue("store");
  }

  async store() {
    this.ctx.storage.sql.exec(`UPDATE transcript SET ... WHERE call_control_id = ?`, ...);
    await this.env.REGISTRY.idFromName("global").record(row);  // cross-call index
    await this.queue("notify");
  }

  async notify() {
    await this.env.TELNYX.messages.send({ from: SMS_FROM, to: SMS_TO, text: state.summary });
    await this.setState({ ...state, phase: "done" });
  }
}

export class TranscriptRegistry extends Agent<...> {
  async record(row) { /* INSERT OR REPLACE INTO transcripts ... */ }
  async list(limit) { /* SELECT * FROM transcripts ORDER BY started_at DESC LIMIT ? */ }
  async get(id)     { /* SELECT * FROM transcripts WHERE call_control_id = ? */ }
}
```

### `src/index.ts` — The Webhook Router

Drives the transcription pipeline by dispatching Call Control webhook events to the per-call actor:

```typescript
if (eventType === "call.initiated") {
  await stub.recordStart(callControlId, from, to);
  await answerCall(apiKey, callControlId);
}

if (eventType === "call.answered") {
  await speakText(apiKey, callControlId, GREETING);
}

if (eventType === "call.speak.ended") {
  await stopTranscription(apiKey, callControlId);  // defensive
  await stub.setTranscribing();
  await startTranscription(apiKey, callControlId);  // streaming STT
}

if (eventType === "call.transcription") {
  const { transcript, is_final } = payload.transcription_data;
  await stub.appendTranscript(transcript, is_final !== false);
}

if (eventType === "call.hangup") {
  await stopTranscription(apiKey, callControlId);
  await stub.onHangup();  // queue(summarize) → store → notify
}
```

### `telnyx.toml` — Config

```toml
[[actors]]
binding = "TRANSCRIBE"
type = "TranscribeAgent"

[[actors]]
binding = "REGISTRY"
type = "TranscriptRegistry"

[telnyx]
binding = "TELNYX"  # pre-authenticated client — no API key in code for inference/SMS

[[secrets]]
binding = "TELNYX_API_KEY"
name = "TELNYX_API_KEY"  # used for Call Control REST (answer, speak, transcription)

[env_vars]
AI_MODEL = "zai-org/GLM-5.2"
SMS_FROM = "+16282564655"
SMS_TO   = "+17177247292"
```

### Agent SDK Primitives

| Primitive | Method | Purpose |
|-----------|--------|---------|
| Durable State | `this.setState()` / `this.getState()` | Per-call transcript accumulation (segments, transcriptText, phase) |
| Pipeline | `this.queue("summarize")` / `this.queue("store")` / `this.queue("notify")` | Non-blocking finalize stages after hangup — survive restarts |
| Actor-Local SQL | `this.ctx.storage.sql.exec(...)` | Per-call transcript row + shared `TranscriptRegistry` for cross-call listing |
| Telnyx Binding | `this.env.TELNYX.ai.openai.chat.createCompletion()` | Zero-credential AI inference for the summary |
| Telnyx Binding | `this.env.TELNYX.messages.send()` | Zero-credential SMS delivery |

### Why Streaming Transcription Instead of `gather(using=speech)`

The Call Control `gather` action captures DTMF digits, not speech-to-text. The `gather_using_ai` action runs Telnyx's hosted AI assistant — but this example doesn't want a conversation, just a transcript. So we use **streaming transcription** (`transcription_start` with the Telnyx engine on the inbound track) for STT, which delivers the caller's speech as text that we accumulate into durable state — no LLM-in-the-loop, no TTS replies, just transcribe → store → summarize on hangup.

### Why Two Actors (TranscribeAgent + TranscriptRegistry)

Each `TranscribeAgent` instance owns one call's state + per-call SQL. There's no built-in way to list SQL rows across per-call actors (each actor's `this.ctx.storage.sql` is private). So we add a second actor — `TranscriptRegistry`, a single shared instance keyed `"global"` — that each per-call agent upserts into on hangup via `this.env.REGISTRY.idFromName("global").record(row)`. Then `GET /transcripts` reads from the registry actor; `GET /transcripts/:id` reads from the registry actor; per-call `GET /debug/state` reads from the per-call actor. Per-call SQL remains the source of truth for any single call; the registry is a listable index.

### Why a Queue-Based Pipeline on Hangup (Not Inline Awaits)

The webhook handler returns `200` immediately on `call.hangup` (Telnyx retries if the webhook doesn't return fast). The heavy work — LLM inference, SQL upsert, SMS send — happens inside the actor via `this.queue("summarize")`, `this.queue("store")`, `this.queue("notify")`. These stages run as separate actor turns, survive restarts, and don't block the webhook. If inference takes 8 seconds, the caller has already hung up and Telnyx has already moved on — the actor keeps running.

## Step 2: Deploy

```bash
npm install
telnyx-edge ship
```

## Step 3: Point your Call Control webhook

In the [Telnyx Portal](https://portal.telnyx.com):
1. Create or edit a Call Control application assigned to your Telnyx number
2. Set the **Webhook URL** → `https://edge-call-transcription-agent-<id>.telnyxcompute.com/webhooks/voice`

## Step 4: Test

### Health

```bash
curl https://edge-call-transcription-agent-<id>.telnyxcompute.com/health/liveness
```

### Real call (requires Call Control application)

1. Call your Telnyx number from your phone
2. The agent answers, speaks a short greeting, and starts streaming STT
3. Speak normally — your speech is appended to the actor's durable transcript
4. Hang up — the actor queues `summarize` → `store` → `notify`
5. Within a few seconds you receive an SMS with the call summary
6. The transcript + summary are persisted in the registry actor's SQL

### Inspect call state

```bash
curl "https://edge-call-transcription-agent-<id>.telnyxcompute.com/debug/state?call_control_id=<your_call_id>"
```

### List recent transcripts

```bash
curl https://edge-call-transcription-agent-<id>.telnyxcompute.com/transcripts
```

### Fetch a specific transcript

```bash
curl https://edge-call-transcription-agent-<id>.telnyxcompute.com/transcripts/<call_control_id>
```

## Going to Production

- **Webhook signature verification** — verify the `telnyx-signature-ed25519` header before processing
- **Multi-track transcription** — set `transcription_tracks: "both"` if you want the agent's greeting transcribed too (currently `inbound` only = caller audio)
- **Long calls** — consider capping `turnCount` or `transcriptText` length to bound LLM token cost
- **SMS delivery to caller** — set `SMS_TO` per call from `state.from` if you want to text the summary back to the caller rather than a fixed recipient
- **Per-caller history** — change the per-call actor's keying from `call_control_id` to `from_number` to keep a single actor per caller across multiple calls
- **Webhook retries** — make `onHangup` idempotent (it is: phase guards prevent re-running the pipeline)
- **Cost tracking** — capture `completion.usage` from the LLM response and store tokens-per-call in state + SQL

## Run

```bash
npm install
telnyx-edge ship
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/edge-call-transcription-agent/README.md)
- [Agent SDK Overview](https://developers.telnyx.com/docs/agent-sdk)
- [Agent SDK Quickstart](https://developers.telnyx.com/docs/agent-sdk/quickstart)
- [Roll Your Own Agent](https://developers.telnyx.com/docs/agent-sdk/examples/roll-your-own)
- [Stateful Actors Quick Start](https://developers.telnyx.com/docs/edge-compute/stateful-actors/quick-start)
- [Call Control API Reference](https://developers.telnyx.com/api-reference/call-control)
- [Streaming Transcription Guide](https://developers.telnyx.com/docs/voice/programmable-voice/transcription)
- [AI Inference Guide](https://developers.telnyx.com/docs/inference)
- [Messaging Guide](https://developers.telnyx.com/docs/messaging)
- [Telnyx Developer Docs](https://developers.telnyx.com)
- [Telnyx Portal](https://portal.telnyx.com)
