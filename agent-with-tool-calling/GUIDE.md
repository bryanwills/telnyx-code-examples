# Guide

This example is built around a durable `ToolAgent` actor.

## Files

- `src/index.ts`: HTTP routing, demo routes, webhook verification, and actor lookup.
- `src/tool-agent.ts`: Agent SDK class, tool definitions, tool dispatch, SQL ledger, and final replies.
- `src/types.ts`: Edge environment, webhook, state, and event types.
- `src/demo-html.ts`: Browser simulator.
- `telnyx.toml`: Edge bindings, secrets, and environment variables.

## Actor routing

The fetch handler normalizes every sender into a stable actor name:

```ts
function actorNameForPhone(phone: string): string {
  return `phone-${phone.replace(/\D/g, "")}`;
}
```

That gives each sender one durable actor instance with its own message history, state, queued work, and SQL tables.

## Tool loop

`receive` stores the user message and queues `process`.

`process` sends the current history to Telnyx Inference with `tools` and `tool_choice: "auto"`.

When the model returns tool calls, the actor:

1. Appends the assistant tool-call turn with `messages.append`.
2. Dispatches each tool through `dispatchToolOnce`.
3. Stores the result in `tool_log`.
4. Appends a `role: "tool"` message with the matching `toolCallId`.
5. Queues `process` again so the model can write a final user-facing reply.

## Idempotency

Inbound webhook events are deduped with a `webhook_events` primary key.

Tool results are stored by `tool_call_id` in `tool_log`. If a retry sees a completed row, it returns the stored result instead of dispatching again.

Voice calls pass `command_id: toolCallId` to make retries easier to correlate.

Production SMS still needs care around crash-after-send-before-log behavior. This example suppresses repeat dispatch after a completed result is logged, and uses mocked SMS by default.

## Demo and production switches

`DEMO_MODE` controls whether the browser routes are exposed.

`SMS_TRANSPORT` controls SMS delivery:

- `demo`: log `send_sms` results without sending carrier SMS.
- `production`: call `env.TELNYX.messages.send`.

Voice calls are separate. `make_call` always uses `env.TELNYX.calls.dial` when `CALL_CONTROL_APP_ID` is configured.

## SMS behavior

The `send_sms` tool validates `to` and `body` before dispatch. In demo mode, it returns:

```json
{
  "ok": true,
  "tool": "send_sms",
  "status": "mocked"
}
```

In production mode, it calls `env.TELNYX.messages.send({ from, to, text })`. If Telnyx accepts the message, the tool result contains the Telnyx message ID. If Telnyx rejects the request, the tool returns `ok: false` with the error instead of breaking the tool loop.

## Voice behavior

The `make_call` tool validates `to`, requires `CALL_CONTROL_APP_ID`, and calls `env.TELNYX.calls.dial`. The Call Control Application must have an outbound voice profile assigned, and the `from` number must be assigned to that application.
