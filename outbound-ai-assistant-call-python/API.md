# API Reference

## `GET /health`

Returns service health and missing configuration values.

## `POST /calls/outbound`

Starts an outbound call.

```json
{
  "to": "+15551234567"
}
```

## `POST /webhooks/telnyx`

Receives Telnyx call lifecycle webhooks.

Handled events:

- `call.answered`
- `call.hangup`

## `GET /sessions`

Lists in-memory call sessions.
