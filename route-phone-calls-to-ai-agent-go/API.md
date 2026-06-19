# API Reference

This server exposes two HTTP routes. The webhook route consumes Telnyx Call Control events and may issue a Telnyx Voice API command in response.

## `GET /health`

Liveness probe.

### Request

No parameters.

### Response `200`

```json
{
  "status": "ok"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## `POST /webhooks/call`

Receives Telnyx Call Control webhook events. The body is bound to a `WebhookPayload` struct; the handler branches on `data.event_type`.

### Request

```json
{
  "data": {
    "event_type": "call.initiated",
    "call_control_id": "v3:abc123",
    "from": "+12125551234",
    "to": "+13105559876"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.event_type` | `string` | **yes** | Call lifecycle event. Recognized values: `call.initiated`, `call.answered`, `call.hangup`, `call.dtmf.received`. |
| `data.call_control_id` | `string` | **yes** | Unique identifier for the call. Used to issue the Answer Call command. |
| `data.from` | `string` | no | Caller number in E.164 format. |
| `data.to` | `string` | no | Destination number in E.164 format. |
| `data.state` | `string` | no | Current call state. |
| `data.direction` | `string` | no | Call direction (`inbound` / `outbound`). |
| `data.start_time` | `string` | no | Call start timestamp. |
| `data.answer_time` | `string` | no | Call answer timestamp. |
| `data.end_time` | `string` | no | Call end timestamp. |
| `data.disconnect_code` | `string` | no | Reason code reported on `call.hangup`. |

### Response `200`

The response message varies by event type.

For `call.initiated` (after answering the call):

```json
{
  "message": "Call answered",
  "call_control_id": "v3:abc123"
}
```

For `call.answered`:

```json
{
  "message": "Call answered event processed",
  "call_control_id": "v3:abc123"
}
```

For `call.hangup`:

```json
{
  "message": "Call hangup event processed",
  "call_control_id": "v3:abc123"
}
```

For `call.dtmf.received`:

```json
{
  "message": "DTMF event processed",
  "call_control_id": "v3:abc123"
}
```

For any unrecognized `event_type`:

```json
{
  "message": "Event received"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/call \
  -H "Content-Type: application/json" \
  -d '{"data": {"event_type": "call.initiated", "call_control_id": "v3:abc123", "from": "+12125551234", "to": "+13105559876"}}'
```

---

## Telnyx API Endpoints Called

The webhook handler calls the Telnyx Voice API when a `call.initiated` event arrives.

| SDK Call | HTTP Endpoint | Purpose |
|----------|---------------|---------|
| `client.Calls.Answer(&telnyx.CallAnswerParams{CallControlID: ...})` | `POST /v2/calls/{call_control_id}/actions/answer` | Answer the inbound call. -- [API reference](https://developers.telnyx.com/api-reference/calls/answer-call) |

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success — webhook acknowledged (and call answered, for `call.initiated`) |
| `400` | Bad request — webhook body could not be parsed as JSON |
| `500` | Server error — the Answer Call command failed |
