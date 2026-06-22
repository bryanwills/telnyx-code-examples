# Route Phone Calls to an AI Agent (Ruby / Sinatra)

Receive inbound Telnyx Call Control webhooks in a Sinatra app, verify the Ed25519 signature, then answer the call and hand it off to a Telnyx AI assistant.

## Why Telnyx

Telnyx is an **AI Communications Infrastructure** platform — voice, messaging, SIP, AI assistants, and IoT on one private, global network. You get programmable [Voice AI agents](https://telnyx.com/products/voice-ai-agents), a developer-first webhook event model, and pay-as-you-go pricing, all from a single API and SDK.

## Telnyx API Endpoints Used

- **Call Control: Answer** — `POST /v2/calls/{call_control_id}/actions/answer` — SDK: `client.calls.actions.answer(call_control_id)`
- **Call Control: Start AI Assistant** — `POST /v2/calls/{call_control_id}/actions/start_ai_assistant` — SDK: `client.calls.actions.start_ai_assistant(call_control_id, assistant: { id: ... })`

See [API.md](./API.md) for the typed request/response reference.

## Telnyx Webhook Events

This app receives Call Control webhook events on `POST /webhooks/voice`:

- `call.initiated` — a new inbound call arrived; the app answers it.
- `call.answered` — the leg is live; the app routes the caller to the AI assistant.
- `call.hangup` — the call ended; the app logs the cause.

## Architecture

```
  Inbound phone call
        │
        ▼
  Telnyx Call Control  ──POST /webhooks/voice──►  Sinatra app (app.rb)
        ▲                                              │
        │                                   1. verify Ed25519 signature
        │                                      over "<timestamp>|<raw body>"
        │                                   2. parse data.payload
        │                                   3. dispatch on data.event_type
        │                                              │
        │  client.calls.actions.answer   ◄────────────┤  (call.initiated)
        │  client.calls.actions.start_ai_assistant ◄──┘  (call.answered)
        ▼
  Caller talks to the Telnyx AI assistant
```

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `TELNYX_API_KEY` | `string` | `KEY0123456789ABCDEF` | **yes** | Telnyx API v2 key used to issue Call Control commands | [Portal → Keys & Credentials](https://portal.telnyx.com) |
| `TELNYX_PUBLIC_KEY` | `string` | `base64-encoded key` | **yes** | Base64 Ed25519 public key used to verify webhook signatures | [Portal → Keys & Credentials → Public Key](https://portal.telnyx.com) |
| `TELNYX_ASSISTANT_ID` | `string` | `assistant_abc123` | **yes** | The AI assistant answered calls are routed into | [Portal → AI Assistants](https://portal.telnyx.com) |
| `PORT` | `number` | `4567` | no | Local port for the Sinatra server (defaults to `4567`) | — |

## Setup

> Telnyx's Ruby SDK requires **Ruby 3.2+**. macOS system Ruby (2.6) will not work; install a current Ruby (e.g. via `rbenv` or `asdf`) first.

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/route-phone-calls-to-ai-agent-ruby
cp .env.example .env       # ← fill in your credentials
bundle install
ruby app.rb                # starts on http://localhost:4567
```

### Webhook configuration

1. Expose your local server with a tunnel:

   ```bash
   ngrok http 4567
   ```

2. In the [Telnyx Portal](https://portal.telnyx.com), open your **Call Control Application** and set the **Webhook URL** to:

   ```
   https://<your-subdomain>.ngrok.io/webhooks/voice
   ```

3. Assign your inbound phone number to that Call Control Application so calls trigger the webhook.

## API Reference

### `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. The handler verifies the Ed25519 signature on the raw body before parsing.

**Required headers**

| Header | Description |
|--------|-------------|
| `telnyx-signature-ed25519` | Base64 Ed25519 signature of `"<timestamp>|<raw body>"` |
| `telnyx-timestamp` | Unix seconds; rejected if more than 300s skewed (replay protection) |

**Responses**

| Status | Meaning |
|--------|---------|
| `200` | Event accepted (`{"status":"ok"}`) |
| `400` | Body was not valid JSON |
| `401` | Missing/invalid signature, or stale timestamp |

### `GET /health`

Liveness probe. Returns `200` with `{"status":"ok"}`.

Full typed reference: [API.md](./API.md).

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 invalid signature` | `TELNYX_PUBLIC_KEY` missing/wrong, or body altered by a proxy | Copy the exact base64 Public Key from the Portal; ensure no middleware rewrites the request body before this handler reads it. |
| `401 invalid signature` on every request, clock looks fine | Server clock drift beyond the 300s replay window | Sync the host clock (NTP). |
| Webhook never arrives | Local server not publicly reachable, or number not on the Call Control App | Run a tunnel (ngrok) and confirm the Portal webhook URL and number assignment. |
| Logs show "authentication failed" | Invalid `TELNYX_API_KEY` | Verify the key in the Portal; no quotes/trailing spaces in `.env`; restart after editing. |
| AI assistant never starts | `TELNYX_ASSISTANT_ID` unset | Set it to a valid assistant ID from Portal → AI Assistants. |
| `LoadError` on `require "telnyx"` | `standardwebhooks` not installed (telnyx 5.x requires it at load time) | Run `bundle install`; the Gemfile pins `standardwebhooks`. |

## Related Examples

- [Make an Outbound Phone Call (Ruby)](../make-outbound-phone-call-ruby)
- [Send SMS (Ruby)](../send-sms-ruby)
- [Route Phone Calls to an AI Agent (Node.js)](../route-phone-calls-to-ai-agent-nodejs)
- [Route Phone Calls to an AI Agent (Go)](../route-phone-calls-to-ai-agent-go)
- [Route Phone Calls to an AI Agent (Python)](../route-phone-calls-to-ai-agent-python)

## Resources

- [Call Control guide](https://developers.telnyx.com/docs/voice/programmable-voice/call-control)
- [Start AI Assistant guide](https://developers.telnyx.com/docs/voice/programmable-voice/ai-assistant-start)
- [Answer Call API reference](https://developers.telnyx.com/api-reference/call-commands/answer-call)
- [Start AI Assistant API reference](https://developers.telnyx.com/api-reference/call-commands/call-control-start-ai-assistant)
- [Webhook signature verification](https://developers.telnyx.com/docs/development/dev-tools/webhook-signing)
- [Telnyx Ruby SDK](https://developers.telnyx.com/development/sdk/ruby)
- [Voice AI Agents product](https://telnyx.com/products/voice-ai-agents)
- [Voice pricing](https://telnyx.com/pricing/call-control)
