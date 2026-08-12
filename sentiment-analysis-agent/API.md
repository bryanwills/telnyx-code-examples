# API Reference

## `GET /health`

Returns a small health payload.

```json
{
  "ok": true,
  "demo": true
}
```

## `GET /`

Available only when `DEMO_MODE = "true"`. Serves the browser simulator.

## `POST /send`

Available only when `DEMO_MODE = "true"`. Simulates an inbound SMS without using carrier transport.

Request:

```json
{
  "from": "+15551234567",
  "text": "this is broken and nobody is helping me"
}
```

Response:

```json
{
  "ok": true
}
```

The route calls:

```ts
env.SENTIMENT.idFromName(from).receive({
  text,
  from,
  to: env.DEMO_FROM_NUMBER,
  eventId: `demo:${crypto.randomUUID()}`
});
```

## `GET /events`

Available only when `DEMO_MODE = "true"`. Reads the actor-local SQL sentiment log for one sender.

Query parameters:

| Parameter | Required | Description |
| --- | --- | --- |
| `from` | no | Sender phone number. Defaults to `DEMO_SENDER_NUMBER`. |
| `limit` | no | Max rows, capped at 100. |

Response:

```json
{
  "events": [
    {
      "id": 1,
      "sender": "+15551234567",
      "message": "this is broken and nobody is helping me",
      "label": "negative",
      "score": 0.91,
      "escalated": true,
      "reply": "I'm sorry this has been frustrating. I've flagged this for our team to review.",
      "at": 1786480000000
    }
  ]
}
```

## `POST /reset`

Available only in demo mode. Clears the actor-local SQL sentiment log for one sender so the browser demo can start blank.

Request:

```json
{
  "from": "+15551234567"
}
```

Response:

```json
{
  "ok": true,
  "from": "+15551234567"
}
```

## `POST /webhooks/messaging`

Production Telnyx Messaging webhook endpoint. Also accepts `POST /`.

Expected event:

```json
{
  "data": {
    "id": "evt_...",
    "event_type": "message.received",
    "payload": {
      "from": { "phone_number": "+15551234567" },
      "to": [{ "phone_number": "+15557654321" }],
      "text": "I need help"
    }
  }
}
```

When `DEMO_MODE = "false"`, this route verifies the raw webhook body with `telnyx.webhooks.unwrap()` and the `TELNYX_PUBLIC_KEY` secret before processing.

Response:

```json
{
  "ok": true
}
```

Non-`message.received` events are acknowledged and ignored:

```json
{
  "ignored": true,
  "event_type": "message.finalized"
}
```
