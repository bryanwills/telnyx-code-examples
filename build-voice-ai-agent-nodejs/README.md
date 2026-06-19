---
name: build-voice-ai-agent
title: "Build a Voice AI Agent"
description: "Build a complete voice AI agent with Telnyx — answer inbound calls, transcribe speech, generate replies with Telnyx Inference, and speak them back via Call Control."
language: nodejs
framework: express
telnyx_products: [Voice, Inference]
channel: [voice]
---

# Build a Voice AI Agent

Build a complete voice AI agent with Telnyx — answer inbound calls, transcribe speech, generate replies with Telnyx Inference, and speak them back via Call Control.

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, AI inference, speech processing, and telephony run on the same private, global network. Inference is co-located with the telephony switch, so the speech-to-LLM-to-speech loop avoids the 30-80ms vendor boundaries you hit when stitching together separate STT, LLM, and TTS providers, and you get one bill and one SLA for the whole stack.

## Telnyx API Endpoints Used

- **Chat Completions (Inference)**: `POST /v2/ai/chat/completions` — [API reference](https://developers.telnyx.com/api/inference/inference-embedding/post-chat-completions)
- **Answer Call**: `POST /v2/calls/{call_control_id}/actions/answer` — [API reference](https://developers.telnyx.com/api/call-control/answer-call)
- **Speak Text (TTS)**: `POST /v2/calls/{call_control_id}/actions/speak` — [API reference](https://developers.telnyx.com/api/call-control/speak-call)
- **Gather Using Speech**: `POST /v2/calls/{call_control_id}/actions/gather` — [API reference](https://developers.telnyx.com/api/call-control/gather-call)

## Architecture

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
   ┌─────────┴───────────────────────────┐
   │                                       │
   ▼                                       ▼
  speak (TTS) ──► gather (STT) ──► Telnyx Inference (LLM)
   ▲                                       │
   └───────────── reply spoken to caller ──┘
```

### Call lifecycle

1. `call.initiated` — answer the inbound call
2. `call.answered` — greet the caller with TTS (`speak`)
3. `call.speak.ended` — start listening for speech (`gather`)
4. `call.gather.ended` — send transcript to Telnyx Inference, speak the reply, loop back to step 3
5. `call.hangup` — clear the conversation history for that call

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key (needs Inference + Call Control access) | [Portal](https://portal.telnyx.com/api-keys) |
| `AI_MODEL` | `string` | `meta-llama/Llama-3.3-70B-Instruct` | no | Inference model used for replies | [Inference docs](https://developers.telnyx.com/docs/inference) |
| `SYSTEM_PROMPT` | `string` | `You are a helpful voice AI agent...` | no | System prompt that sets the agent's personality | — |
| `TRANSFER_NUMBER` | `string` | `+12125551234` | no | Phone number for human transfer (E.164) | — |
| `PORT` | `number` | `5000` | no | Port the Express server listens on | — |

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/build-voice-ai-agent-nodejs
cp .env.example .env    # ← fill in your credentials
npm install
node server.js          # starts on http://localhost:5000
```

### Webhook Configuration

1. Expose your local server:

   ```bash
   ngrok http 5000
   ```

2. Copy the HTTPS URL and configure in the [Telnyx Portal](https://portal.telnyx.com):

   - **Call Control Application** → Webhook URL → `https://<id>.ngrok.io/webhooks/voice`

3. Assign your inbound voice number to that Call Control Application, then call the number.

## API Reference

### `POST /webhooks/voice`

Receives Call Control webhook events from Telnyx and drives the call: answer, greet, listen, respond, and clean up. Telnyx calls this endpoint — you do not call it directly — but you can simulate an event to verify routing:

```bash
curl -X POST http://localhost:5000/webhooks/voice \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "event_type": "call.gather.ended",
      "call_control_id": "v3:abc123",
      "speech": { "result": "What are your hours?" }
    }
  }'
```

**Response:**

```json
{
  "status": "responding",
  "response": "We're open 9am to 5pm, Monday through Friday."
}
```

The `status` field varies by `event_type`: `answering`, `greeting`, `listening`, `reprompting`, `responding`, `call_ended`, or `event_received`.

### `GET /health`

Liveness check that also reports the number of active calls being tracked.

```bash
curl http://localhost:5000/health
```

**Response:**

```json
{
  "status": "ok",
  "active_calls": 0
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Agent does not answer | Webhook URL not set or ngrok tunnel down | Set the Call Control Application webhook to `https://<id>.ngrok.io/webhooks/voice` and confirm ngrok is running |
| `401 Unauthorized` | Invalid `TELNYX_API_KEY` | Generate a new key at [portal.telnyx.com/api-keys](https://portal.telnyx.com/api-keys) |
| No AI response / `Inference API error` | Key lacks Inference access or model name is wrong | Confirm the key has Inference permissions and `AI_MODEL` is a valid model id |
| Speech not recognized | Caller silence shorter than the gather timeout, or wrong language | Increase `end_silence_timeout_secs` in the `gather` call or check `language_code` |
| Connection refused on port 5000 | App isn't running or port in use | Run `node server.js` and ensure no other process uses port 5000 |

## Related Examples

- [build-voice-ai-agent-python](../build-voice-ai-agent-python/) — same agent in Python
- [route-phone-calls-to-ai-agent-nodejs](../route-phone-calls-to-ai-agent-nodejs/) — route inbound calls to an AI agent
- [run-llm-inference-nodejs](../run-llm-inference-nodejs/) — call Telnyx Inference directly
- [create-ai-assistant-nodejs](../create-ai-assistant-nodejs/) — managed AI Assistant alternative

## Resources

- [Voice API Guide](https://developers.telnyx.com/docs/voice)
- [Telnyx Inference Guide](https://developers.telnyx.com/docs/inference)
- [Call Control API Reference](https://developers.telnyx.com/api/call-control/answer-call)
- [Node.js SDK](https://developers.telnyx.com/development/sdk/node)
- [Voice AI Agents](https://telnyx.com/products/voice-ai-agents)
- [Pricing](https://telnyx.com/pricing/call-control)
