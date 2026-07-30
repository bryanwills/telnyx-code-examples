# API Reference

## `POST /webhooks/voice`

Receives Telnyx Voice API webhooks and starts the configured Telnyx AI Assistant on answered inbound calls.

The endpoint validates Telnyx webhook signatures when `TELNYX_PUBLIC_KEY` is set.

### Important Events

| Event | Behavior |
|---|---|
| `call.initiated` | Stores sanitized call state and answers inbound calls. |
| `call.answered` | Starts the configured AI Assistant with `ai_assistant_start`. |
| `call.payment.progress` / `call_payment_progress` | Records Pay over Voice progress with masked payment fields only. |
| `call.payment.completed` / `call_payment_completed` | Records payment completion with masked payment fields only. |
| `call.conversation.ended` | Records high-level assistant lifecycle status. |
| `call.conversation_insights.generated` | Records high-level assistant lifecycle status. |
| `call.hangup` | Cleans up active call state. |

## `POST /webhooks/payment-processor`

Mock Pay Connector processor endpoint. Telnyx Pay over Voice calls this endpoint after collecting card details through the protected keypad flow.

### Success Response

```json
{
  "charge_id": "ch_demo_1760000000",
  "amount": "40.00",
  "error_code": null,
  "error_message": null
}
```

Cards ending in `0002` simulate a decline:

```json
{
  "error_code": "card_declined",
  "error_message": "the card was declined."
}
```

## `GET /health`

Returns runtime configuration state and dashboard milestones.

## `GET /events`

Returns sanitized local audit events.

## `GET /sessions`

Returns completed payment session summaries.
