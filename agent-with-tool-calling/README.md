---
name: agent-with-tool-calling
title: "Agent with Tool Calling"
description: "Build a Telnyx Edge Compute Agent SDK app where an LLM chooses send_sms, make_call, and check_status tools, dispatches them with toolCallId, and returns a final response."
language: nodejs
framework: telnyx-edge
telnyx_products: [Edge Compute, AI Inference, Messaging, Voice]
channel: [sms, voice]
---

# Agent with Tool Calling

Build a Telnyx Edge Compute agent that lets GLM-5.2 choose tools, execute them inside a durable `ToolAgent`, and pass tool results back to the model for a final response.

The sample includes a browser simulator so you can test the Agent SDK tool-dispatch loop before production SMS compliance is ready. In demo mode, only the SMS carrier transport is mocked; Edge Compute, StatefulActor storage, Telnyx Inference, tool calling, and Call Control dispatch remain real when configured.

## Telnyx APIs Used

- **Edge Compute**: deploys the HTTP handler and `ToolAgent` actor.
- **Agent SDK**: `class ToolAgent extends Agent`.
- **Telnyx Inference binding**: `this.env.TELNYX.ai.openai.chat.createCompletion()`.
- **Telnyx Messaging binding**: `this.env.TELNYX.messages.send()`.
- **Telnyx Call Control binding**: `this.env.TELNYX.calls.dial()`.
- **Actor-local SQL**: `this.ctx.storage.sql`.
- **Messaging webhooks**: `message.received`.

## Architecture

```text
User message
    |
    v
Edge fetch handler
    |
    v
ToolAgent.receive()
  - dedup webhook or demo event
  - append user message
  - queue process()
    |
    v
ToolAgent.process()
  - call Telnyx Inference with tool definitions
  - append assistant tool-call message
  - dispatch send_sms, make_call, or check_status
  - append role=tool result with the same toolCallId
  - call the model again for the final response
```

## Why Telnyx

Telnyx gives you AI, messaging, voice, and Edge Compute behind one authenticated binding. The deployed function calls Telnyx Inference, Messaging, and Call Control with `this.env.TELNYX`, so the application code does not manage separate runtime API keys for those services.

## Environment Variables

`telnyx.toml` defaults to a safe demo configuration:

| Variable | Type | Example | Required | Description | Where to get it |
|----------|------|---------|----------|-------------|-----------------|
| `DEMO_MODE` | `string` | `true` | no | Enables the browser simulator routes when not set to `false`. | - |
| `SMS_TRANSPORT` | `string` | `demo` | no | Use `demo` to log SMS tool calls without carrier delivery. Use `production` for real SMS. | - |
| `DEMO_FROM_NUMBER` | `string` | `+15557654321` | yes | Telnyx number the demo treats as the inbound destination and outbound `from` number. | [My Numbers](https://portal.telnyx.com/numbers/my-numbers) |
| `DEMO_SENDER_NUMBER` | `string` | `+15551234567` | no | Default simulated user phone number for the browser UI. | - |
| `CALL_CONTROL_APP_ID` | `string` | `1234567890` | voice only | Voice API / Call Control Application ID used by `make_call`. | [Call Control Apps](https://portal.telnyx.com/call-control/applications) |
| `MAX_TOOL_ITERATIONS` | `number` | `3` | no | Safety cap for queued model/tool iterations. | - |
| `MODEL` | `string` | `zai-org/GLM-5.2` | no | Telnyx Inference model name. | [Inference models](https://developers.telnyx.com/docs/inference/models) |

For production Messaging webhooks, also store `TELNYX_PUBLIC_KEY` as an Edge secret.

## Setup

```bash
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples/agent-with-tool-calling
npm install
npm run typecheck
npm run types
```

Authenticate the Edge CLI:

```bash
telnyx-edge auth api-key set "$TELNYX_API_KEY"
telnyx-edge status
```

For a fresh deployable function, scaffold with the CLI so Telnyx assigns a function ID:

```bash
telnyx-edge new-func --actor --name=agent-with-tool-calling
```

Then copy this sample's `src/`, docs, dependencies, and binding blocks into the generated project. Keep the generated `[edge_compute]` `func_id` if the CLI adds one.

## Demo Mode

Ship the function:

```bash
telnyx-edge ship
```

Open the deployed function URL in a browser. Try:

- `Text +13125550001 hi from the Telnyx agent`
- `Call me at +13125550001`
- `Did the SMS send?`

In demo mode:

- `POST /send` simulates inbound SMS.
- `GET /events` reads the actor-local conversation and tool ledger.
- `send_sms` returns `status: "mocked"` and does not send carrier SMS.
- `make_call` places a real Call Control call only when `CALL_CONTROL_APP_ID` and `DEMO_FROM_NUMBER` are configured for voice.

## Production SMS

To switch the SMS tool to real carrier delivery:

1. Set `SMS_TRANSPORT = "production"` in `telnyx.toml`.
2. Store the Telnyx webhook public key:

   ```bash
   telnyx-edge secrets add TELNYX_PUBLIC_KEY "<public key from Mission Control>"
   ```

3. Point your Messaging Profile webhook to:

   ```text
   https://<your-function>.telnyxcompute.com/webhooks/messaging
   ```

4. Confirm the `from` number is SMS-capable, assigned to the Messaging Profile, and approved for toll-free or 10DLC requirements when applicable.

When production SMS is enabled, `send_sms` calls:

```ts
this.env.TELNYX.messages.send({
  from: fromNumber,
  to,
  text: body
});
```

Carrier compliance cannot be bypassed in code. Keep `SMS_TRANSPORT = "demo"` until your Messaging Profile and number are ready.

## Real Voice Calls

`make_call` calls:

```ts
this.env.TELNYX.calls.dial({
  connection_id: this.env.CALL_CONTROL_APP_ID,
  from: fromNumber,
  to,
  command_id: toolCallId
});
```

To make real calls:

1. Create or choose a Call Control Application.
2. Assign an outbound voice profile to it.
3. Assign `DEMO_FROM_NUMBER` to that Call Control Application.
4. Set `CALL_CONTROL_APP_ID` in `telnyx.toml`.
5. Ship the function.

## API Reference

See [API.md](./API.md) for endpoint examples.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Browser shows no tool events immediately | Model/tool work runs asynchronously in the actor queue | Wait a few seconds or click refresh |
| SMS shows `status: "mocked"` | `SMS_TRANSPORT` is `demo` | This is expected for safe demos; set `production` only after Messaging setup is complete |
| SMS returns an error in production | Number, Messaging Profile, API, or compliance setup rejected the send | Check the returned tool result and Telnyx Messaging logs |
| Call returns `CALL_CONTROL_APP_ID is not configured` | Voice app ID is missing or still a placeholder | Set `CALL_CONTROL_APP_ID` to a real Call Control Application ID |
| Call Control returns an outbound profile error | The Call Control Application has no outbound voice profile | Assign an outbound voice profile in the Portal |
| Tool loop hits the safety limit | The model repeatedly requested tools instead of writing a final response | Inspect `/events` process log; the sample logs every iteration |

## Related Examples

- [send-sms-nodejs](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/send-sms-nodejs/README.md)
- [receive-sms-webhook-nodejs](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/receive-sms-webhook-nodejs/README.md)
- [make-outbound-phone-call-nodejs](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/make-outbound-phone-call-nodejs/README.md)
- [run-llm-inference-python](https://raw.githubusercontent.com/team-telnyx/telnyx-code-examples/main/run-llm-inference-python/README.md)

## Resources

- [Telnyx Edge Compute](https://developers.telnyx.com/docs/edge-compute)
- [Telnyx Inference](https://developers.telnyx.com/docs/inference)
- [Send Messages](https://developers.telnyx.com/docs/messaging/messages/send-message)
- [Messaging Webhooks](https://developers.telnyx.com/docs/messaging/messages/receiving-webhooks)
- [Call Control](https://developers.telnyx.com/docs/voice/programmable-voice/voice-api-commands-and-resources)
- [Telnyx Portal](https://portal.telnyx.com)
