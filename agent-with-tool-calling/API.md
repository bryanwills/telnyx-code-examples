# API Reference

## `GET /health`

Returns runtime mode information.

```json
{
  "ok": true,
  "demo": true,
  "smsTransport": "demo",
  "voiceConfigured": false,
  "brand": "agent-tools-edge-v1"
}
```

## `GET /version`

Returns the demo brand/version marker.

## `GET /`

Available when `DEMO_MODE` is not `"false"`. Serves the browser simulator.

## `HEAD /`

Available when `DEMO_MODE` is not `"false"`. Returns the same page headers as `GET /` without a response body.

## `POST /send`

Available when `DEMO_MODE` is not `"false"`. Simulates an inbound SMS.

Request:

```json
{
  "from": "+15551234567",
  "text": "Text John at +13125550001 and tell him the meeting moved to 3pm"
}
```

Response:

```json
{
  "ok": true
}
```

## `GET /events`

Available when `DEMO_MODE` is not `"false"`. Reads the actor-local conversation log and tool-call ledger.

Query parameters:

| Parameter | Required | Description |
| --- | --- | --- |
| `from` | no | Sender phone number. Defaults to `DEMO_SENDER_NUMBER`. |
| `limit` | no | Max rows, capped at 100. |

Response:

```json
{
  "toolEvents": [
    {
      "id": 1,
      "tool_call_id": "call_abc",
      "tool": "send_sms",
      "args": {
        "to": "+13125550001",
        "body": "Meeting moved to 3pm"
      },
      "result": {
        "ok": true,
        "tool": "send_sms",
        "status": "mocked",
        "message_id": "demo_call_abc",
        "to": "+13125550001",
        "body": "Meeting moved to 3pm"
      },
      "status": "done",
      "at": 1786480000000
    }
  ],
  "conversation": [
    {
      "id": 1,
      "role": "user",
      "content": "Text John at +13125550001 and tell him the meeting moved to 3pm",
      "at": 1786480000000
    }
  ],
  "processLog": [
    {
      "id": 1,
      "iteration": 0,
      "phase": "after_model",
      "tool_choice": "auto",
      "finish_reason": "tool_calls",
      "tool_calls": [
        {
          "id": "call_abc",
          "name": "send_sms",
          "args": {
            "to": "+13125550001",
            "body": "Meeting moved to 3pm"
          }
        }
      ],
      "note": "model requested tools",
      "at": 1786480000000
    }
  ]
}
```

For a production SMS send accepted by the API, the result uses `status: "sent"` and includes the Telnyx message ID. If Telnyx rejects the request, the tool result uses `ok: false` and includes the error message.

For a Call Control request accepted by the API, the result includes `call_control_id`, `call_leg_id`, and `call_session_id`.

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

When `SMS_TRANSPORT = "production"`, this route verifies the raw webhook body with `telnyx.webhooks.unwrap()` and the `TELNYX_PUBLIC_KEY` secret before processing.

Non-`message.received` events are acknowledged and ignored:

```json
{
  "ignored": true,
  "event_type": "message.finalized"
}
```
