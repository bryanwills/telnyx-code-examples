# API Reference

## `POST /calls/outbound`

Starts an outbound hold-aware call.

```json
{
  "to": "+15551234567",
  "objective": "verify account status",
  "target_company": "example company"
}
```

## `POST /tools/hold-detected`

Assistant tool endpoint for explicit hold detection.

```json
{
  "call_control_id": "v3:...",
  "reason": "caller was placed in a queue",
  "confidence": 0.9
}
```

## `POST /webhooks/telnyx`

Receives call lifecycle and transcription events.

## `GET /sessions`

Lists local sessions.
