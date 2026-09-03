# Guide: Conference Agent Mediator

This guide walks you through the `conference-agent-mediator` sample. The application implements an AI meeting facilitator that joins Telnyx Call Control conferences, transcribes the conversation in real-time, mediates turn-taking so no participant is left out, and sends a post-conference summary via SMS. A WebSocket endpoint streams the live transcript to observers.

Because this sample uses the Telnyx Edge Agent SDK, it runs entirely on Telnyx's edge runtime. There is no separate server process to manage.

## Prerequisites

- A Telnyx account with API access
- A Telnyx number configured for Call Control
- Node.js 18 or later (for local Edge development)
- The Telnyx CLI configured with your account credentials

## Environment setup

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|---|---|
| `TELNYX_API_KEY` | Your Telnyx API key |
| `TELNYX_NUMBER` | The Telnyx number the agent uses to join conferences |
| `OBSERVER_SMS_NUMBER` | Number that receives the post-conference summary |
| `DRY_RUN` | Set to `true` for safe demo mode, `false` for live mode |

## Running the sample

Install dependencies:

```bash
npm install
```

Start the Edge worker locally:

```bash
npx telnyx-edge dev
```

Deploy to Telnyx Edge:

```bash
npx telnyx-edge deploy
```

## Demo mode vs live mode

By default this sample runs in **safe demo mode** (`DRY_RUN=true`). In demo mode:

- The agent joins the conference bridge but does not place outbound calls.
- SMS summaries are logged to the console instead of sent.
- Transcription runs on simulated audio frames so you can test without a live call.

To switch to **live mode**, set `DRY_RUN=false` in your `.env`. In live mode:

- The agent places a real call to join the conference.
- Real SMS messages are sent to `OBSERVER_SMS_NUMBER`.
- Transcription runs on actual conference audio via the Telnyx Media stream.

Always test in demo mode first to avoid unexpected charges.

## How the code is structured

The entry point is `src/index.ts`. It exports the default Edge app handler and wires together four primitives: Call Control, the Agent SDK, Inference bindings, and WebSocket streaming.

### 1. Call Control — conference join and speak

The application uses Telnyx Call Control to:

- Create or join a conference bridge
- Listen to conference audio for transcription
- Inject synthesized speech when the agent needs to prompt a participant

In the Call Control setup section of `src/index.ts`, the handler receives a webhook indicating a conference has started. It calls the Call Control API to have the agent's number dial into the bridge. Once joined, it enables media streaming so the agent receives audio frames for transcription.

The agent uses the `speak` command to inject text-to-speech into the conference. This is how it prompts participants who have not spoken yet.

### 2. Agent SDK — ConferenceAgent with conversation state

The `ConferenceAgent` class extends `Agent` from the Telnyx Edge SDK. It maintains conversation state across the lifecycle of a single conference:

- **Participant tracking** — a map of participant identifiers to timestamps of their last utterance
- **Turn-taking state** — whether the agent has already prompted a given participant
- **Transcript buffer** — the full transcript accumulated for the end-of-call summary

The agent's lifecycle hooks are:

- `onStart` — called when the agent is spawned for a new conference; initializes state
- `onTranscript` — called for each transcription chunk; updates participant timestamps and appends to the transcript buffer
- `onSchedule` — called on a periodic timer; checks for silent participants and triggers a prompt
- `onEnd` — called when the conference ends; generates the summary and sends the SMS

### 3. Inference binding — transcription, summary, and turn detection

The sample uses Telnyx Inference bindings for three AI tasks:

**Real-time transcription:** An STT binding is attached to the media stream. Each audio chunk is transcribed and the result is passed to the agent's `onTranscript` hook. The transcript includes speaker diarization so the agent knows who said what.

**Turn-taking mediation:** On each scheduled tick, the agent sends the current participant state to an LLM binding. The prompt asks the model to identify participants who have not spoken in the last N seconds and suggest a natural prompt. If the model returns a prompt, the agent uses Call Control `speak` to inject it into the conference.

**Post-conference summary:** When the conference ends, the agent sends the full transcript buffer to an LLM binding with a summarization prompt. The model returns a concise summary of decisions, action items, and participation balance.

### 4. WebSocket — live transcript stream for observers

The Edge app exposes a WebSocket route at `/transcript/:conferenceId`. Observers connect to this endpoint to receive a live feed of transcription events.

Internally, the agent publishes each transcript chunk to a pub/sub channel keyed by conference ID. The WebSocket handler subscribes to that channel on connection and forwards messages to the client. This allows multiple observers (for example, a dashboard or note-taking tool) to follow the conversation in real time without joining the call.

## End-to-end flow

1. A conference is created via Call Control. Telnyx sends a webhook to the Edge app.
2. The Edge handler spawns a `ConferenceAgent` for that conference.
3. The agent joins the conference bridge using Call Control and enables media streaming.
4. Audio frames flow to the STT inference binding. Transcribed text is sent to `onTranscript`.
5. The agent updates participant timestamps and publishes each chunk to the WebSocket channel.
6. On a periodic schedule, the agent checks turn-taking via the LLM binding and prompts silent participants.
7. When the conference ends, the agent generates a summary via the LLM binding and sends it via SMS (or logs it in demo mode).

## Verifying it works

After deploying, you can verify the sample by:

1. Starting a Call Control conference on your Telnyx number.
2. Watching the Edge logs for the `ConferenceAgent` spawn and join events.
3. Connecting to the WebSocket endpoint to observe the live transcript.
4. Ending the conference and checking the logs (demo mode) or your SMS inbox (live mode) for the summary.

## Next steps

- [Telnyx Call Control docs](https://developers.telnyx.com/docs/voice/call-control-overview)
- [Telnyx Edge SDK](https://developers.telnyx.com/docs/edge)
- [Telnyx Inference bindings](https://developers.telnyx.com/docs/ai/inference)
- [Telnyx SMS API](https://developers.telnyx.com/docs/messaging)
- [Telnyx WebSocket media streaming](https://developers.telnyx.com/docs/voice/media-streaming)
