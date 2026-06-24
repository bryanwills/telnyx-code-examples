# API Reference

## `GET /health`

Returns app health and dry-run status.

## `GET /scenarios`

Lists available mock IVR scenarios.

## `POST /calls/outbound`

Starts a test run.

```json
{
  "to": "+15551234567",
  "scenario": "support_hold",
  "objective": "reach support and ask for account status"
}
```

## `GET/POST /mock-ivr/{scenario}/start`

Returns TeXML for the first mock IVR prompt.

## `GET/POST /mock-ivr/{scenario}/menu`

Receives DTMF from the mock IVR and returns the next TeXML response.

## `POST /tools/send-dtmf`

Assistant tool endpoint for keypad input.

```json
{
  "digits": "1",
  "reason": "support menu option"
}
```

The response includes `matched_expected` when a test session is active.

## `POST /tools/end-call`

Assistant tool endpoint for ending the test call.

## `GET /test-results`

Returns in-memory sessions and tool events.
