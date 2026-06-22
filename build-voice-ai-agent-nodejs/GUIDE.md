# Build a Voice AI Agent with Telnyx

Build a complete voice AI agent with Telnyx — answer inbound calls, transcribe speech, generate replies with Telnyx Inference, and speak them back via Call Control.

## How It Works

```
  Caller
    │
    ▼
  ┌──────────────────────┐
  │ Telnyx Phone Number  │
  └──────────┬───────────┘
             │ Call Control webhooks
             ▼
  ┌──────────────────────┐
  │  Express App         │
  │  /webhooks/voice     │
  └──────────┬───────────┘
             │
  speak (TTS) ──► gather (STT) ──► Telnyx Inference (LLM) ──► spoken reply
```

## Telnyx Products Used

- **Voice (Call Control)** — answer the call, speak text (TTS), and gather speech (STT)
- **Inference** — generate the agent's replies with an LLM

## API Endpoints

- **Chat Completions (Inference)**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/inference-embedding/post-chat-completions)
- **Answer Call**: `POST /v2/calls/{call_control_id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Speak Text**: `POST /v2/calls/{call_control_id}/actions/speak` — [API reference](https://developers.telnyx.com/api/call-control/speak-call)
- **Gather Using Speech**: `POST /v2/calls/{call_control_id}/actions/gather` — [API reference](https://developers.telnyx.com/api/call-control/gather-call)

## Prerequisites

- Node.js 18+ (the app uses the built-in global `fetch`)
- [Telnyx account](https://portal.telnyx.com/sign-up) with a funded balance
- [API key](https://portal.telnyx.com/api-keys) with Call Control and Inference access
- A [phone number](https://portal.telnyx.com/numbers/my-numbers) enabled for inbound voice
- A [Call Control Application](https://portal.telnyx.com/call-control/applications) with its webhook URL set to your server
- [ngrok](https://ngrok.com) to expose your local server to Telnyx webhooks

## Step 1: Set Up the Project

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/build-voice-ai-agent-nodejs
cp .env.example .env
npm install
```

Edit `.env` with your Telnyx credentials. Only `TELNYX_API_KEY` is required; `AI_MODEL`, `SYSTEM_PROMPT`, `TRANSFER_NUMBER`, and `PORT` have sensible defaults.

## Step 2: Understand the Code

Everything lives in `server.js`. Here's what each piece does.

### Helper Functions

- **`callTelnyxInference(messages)`** — POSTs the conversation to `https://api.telnyx.com/v2/ai/chat/completions` and returns the assistant's text from `choices[0].message.content`.
- **`getAiResponse(callControlId, userInput)`** — keeps per-call conversation history in an in-memory `Map` (seeded with the system prompt), appends the caller's input, calls inference, stores the reply, and trims history to the last ~20 turns.

### All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Handle Call Control events and drive the call |
| `GET`  | `/health` | Liveness check with active-call count |

### The webhook switch

The `/webhooks/voice` handler branches on `data.event_type` to advance the call:

```js
switch (eventType) {
  case "call.initiated":
    if (data.direction === "incoming") {
      await telnyx.calls.actions.answer(callControlId);
    }
    return res.json({ status: "answering" });

  case "call.answered":
    await telnyx.calls.actions.speak(callControlId, {
      payload: "Hi, thanks for calling. How can I help you today?",
      voice: "female",
      language_code: "en-US",
    });
    return res.json({ status: "greeting" });
  // ...
}
```

After each `speak`, Telnyx fires `call.speak.ended`, which triggers a `gather` to listen for the caller. When the caller finishes speaking, `call.gather.ended` carries the transcript in `data.speech.result`, which is sent to inference and spoken back — looping the conversation until `call.hangup`.

## Step 3: Run It

```bash
node server.js
```

The server starts on `http://localhost:5000` (or `PORT`).

In a separate terminal, expose your server for webhooks:

```bash
ngrok http 5000
```

Copy the HTTPS URL and set it in the [Telnyx Portal](https://portal.telnyx.com):

- **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

Then assign your inbound voice number to that application.

## Step 4: Test It

**Health check:**

```bash
curl http://localhost:5000/health
```

**Simulate a speech event** (verifies routing and the inference call):

```bash
curl -X POST http://localhost:5000/webhooks/voice \
  -H "Content-Type: application/json" \
  -d '{"data":{"event_type":"call.gather.ended","call_control_id":"v3:abc123","speech":{"result":"What are your hours?"}}}'
```

Or simply call your Telnyx number and talk to the agent.

## Going to Production

This example uses an in-memory `Map` for conversation history. For production:

- **Conversation store** — replace the in-memory `Map` with Redis so state survives restarts and scales across instances
- **Webhook verification** — validate Telnyx webhook signatures ([docs](https://developers.telnyx.com/docs/api/v2/overview#webhook-signing))
- **Human transfer** — wire up `TRANSFER_NUMBER` to a `transfer` call-control action for escalation
- **Monitoring** — add structured logging and alert on inference/call-control errors
- **Latency** — host the webhook server close to Telnyx infrastructure to keep the speech-to-reply loop tight

## Run

```bash
npm install
node server.js
```

## Resources

- [Source code and reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/build-voice-ai-agent-nodejs/README.md)
- [Typed API reference](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/build-voice-ai-agent-nodejs/API.md)
- [Telnyx Voice Guide](https://developers.telnyx.com/docs/voice)
- [Telnyx Inference Guide](https://developers.telnyx.com/docs/inference)
- [Node.js SDK](https://developers.telnyx.com/development/sdk/node)
- [Telnyx Portal](https://portal.telnyx.com)
