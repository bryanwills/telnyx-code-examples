## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events and drives the call. The app branches on `data.event_type`. Telnyx invokes this endpoint; the request body is the standard Call Control webhook envelope.

### Request

```json
{
  "data": {
    "event_type": "call.gather.ended",
    "call_control_id": "v3:abc123",
    "direction": "incoming",
    "speech": { "result": "What are your hours?" }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | `object` | **yes** | Webhook payload envelope. Returns `400` if absent |
| `data.event_type` | `string` | **yes** | Call Control event, e.g. `call.initiated`, `call.answered`, `call.speak.ended`, `call.gather.ended`, `call.hangup` |
| `data.call_control_id` | `string` | **yes** | Identifier of the call, used for all call-control actions and as the conversation key |
| `data.direction` | `string` | no | `incoming` or `outgoing`; only `incoming` calls are answered (on `call.initiated`) |
| `data.speech.result` | `string` | no | Transcribed caller speech, present on `call.gather.ended` |

### Response `200`

Shape depends on the handled event. Example for `call.gather.ended` with recognized speech:

```json
{
  "status": "responding",
  "response": "We're open 9am to 5pm, Monday through Friday."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | One of `answering`, `greeting`, `listening`, `reprompting`, `responding`, `call_ended`, `event_received` |
| `response` | `string` | The AI-generated reply spoken to the caller. Present only on `responding` |
| `event_type` | `string` | Echoed event type. Present only on `event_received` (unhandled events) |

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice \
  -H "Content-Type: application/json" \
  -d '{"data":{"event_type":"call.gather.ended","call_control_id":"v3:abc123","speech":{"result":"What are your hours?"}}}'
```

---

## `GET /health`

Liveness probe. Reports server status and the count of in-memory conversations currently tracked.

### Request

No parameters.

### Response `200`

```json
{
  "status": "ok",
  "active_calls": 0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | Always `ok` when the server is up |
| `active_calls` | `number` | Number of calls with active conversation history |

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Telnyx APIs Called

The app calls these Telnyx endpoints in response to webhook events.

| When | Telnyx call | Endpoint |
|------|-------------|----------|
| `call.initiated` (incoming) | `telnyx.calls.actions.answer` | `POST /v2/calls/{call_control_id}/actions/answer` |
| `call.answered`, `call.speak.ended` reply, `call.gather.ended` reply | `telnyx.calls.actions.speak` | `POST /v2/calls/{call_control_id}/actions/speak` |
| `call.speak.ended` | `telnyx.calls.actions.gather` | `POST /v2/calls/{call_control_id}/actions/gather` |
| `call.gather.ended` (with speech) | `fetch` to Inference | `POST /v2/ai/chat/completions` |

### Inference request body

```json
{
  "model": "meta-llama/Llama-3.3-70B-Instruct",
  "messages": [
    { "role": "system", "content": "You are a helpful voice AI agent..." },
    { "role": "user", "content": "What are your hours?" }
  ],
  "max_tokens": 150,
  "temperature": 0.7
}
```

The reply text is read from `choices[0].message.content`.

---

## Error Handling

All endpoints return JSON. On error:

```json
{ "error": "Internal error" }
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing `data` payload |
| `500` | Server error — webhook handling or upstream Telnyx/Inference failure |
