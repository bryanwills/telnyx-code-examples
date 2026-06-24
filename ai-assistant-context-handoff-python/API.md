# API Reference

## `POST /calls/outbound`

Starts an outbound call.

## `POST /tools/representative-detected`

Stops the IVR assistant and starts the representative assistant with context.

```json
{
  "reason": "representative answered"
}
```

## `POST /webhooks/telnyx`

Starts the IVR assistant on `call.answered` and cleans up on `call.hangup`.
