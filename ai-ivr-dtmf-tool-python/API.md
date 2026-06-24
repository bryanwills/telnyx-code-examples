# API Reference

## `POST /calls/outbound`

Starts an outbound IVR navigation call.

```json
{
  "to": "+15551234567",
  "objective": "reach the support department"
}
```

## `POST /tools/send-dtmf`

Tool endpoint called by the Telnyx AI Assistant.

```json
{
  "call_control_id": "v3:...",
  "digits": "1",
  "reason": "support menu option"
}
```

If `call_control_id` is omitted, the example uses the most recent active call.

## `GET /media/dtmf/{digit}.wav`

Serves a short generated DTMF tone for demo feedback.
