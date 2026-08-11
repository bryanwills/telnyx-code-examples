## `POST /webhooks/voice`

Receives Telnyx Call Control webhooks and drives the conversation loop.

### Events Handled

#### `call.initiated`

Answers the inbound call and records the start in the actor.

**Request (Telnyx webhook payload):**

```json
{
  "data": {
    "event_type": "call.initiated",
    "payload": {
      "call_control_id": "v3:550e8400-e29b-41d4-a716-446655440000",
      "from": "+17177247292",
      "to": "+16282564655"
    }
  }
}
```

**Response `200`:**

```json
{
  "action": "answering",
  "callControlId": "v3:550e8400-e29b-41d4-a716-446655440000"
}
```

---

#### `call.answered`

Speaks the greeting via Call Control TTS.

**Request:**

```json
{
  "data": {
    "event_type": "call.answered",
    "payload": {
      "call_control_id": "v3:550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

**Response `200`:**

```json
{
  "action": "greeting"
}
```

---

#### `call.speak.ended`

When the greeting or a reply finishes speaking, starts streaming transcription to listen for the caller's next utterance.

| Field | Type | Description |
|-------|------|-------------|
| `data.payload.call_control_id` | `string` | Call ID |
| `data.payload.client_state` | `string` | Base64-encoded `{ speak_stage: "greeting" | "reply" }` |

**Response `200`:**

```json
{
  "action": "listening",
  "speak_stage": "greeting"
}
```

---

#### `call.transcription`

When a final transcript arrives, stops transcription, adds the user speech to conversation history, runs an LLM turn via `this.env.TELNYX.ai.openai.chat.createCompletion()`, and speaks the reply.

| Field | Type | Description |
|-------|------|-------------|
| `data.payload.call_control_id` | `string` | Call ID |
| `data.payload.transcription_data.transcript` | `string` | The transcribed text |
| `data.payload.transcription_data.is_final` | `boolean` | Whether this is a final (not interim) result |

**Response `200`:**

```json
{
  "action": "replying",
  "turn": "what's the weather like"
}
```

---

#### `call.hangup`

Finalizes the call state in durable storage.

**Response `200`:**

```json
{
  "action": "hungup"
}
```

---

## `GET /debug/call`

Inspect actor state for a call — phase, turn count, conversation history count, last message.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `call_control_id` | `string` | **yes** | The Call Control ID of the call to inspect |

**Try it:**

```bash
curl "https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/debug/call?call_control_id=v3:abc123"
```

**Response `200`:**

```json
{
  "state": {
    "callControlId": "v3:abc123",
    "from": "+17177247292",
    "to": "+16282564655",
    "phase": "replying",
    "turnCount": 3,
    "startedAt": 1723372800000,
    "lastTranscript": "what's the weather like",
    "lastReply": "I don't have access to live weather data..."
  },
  "messageCount": 6,
  "lastMessage": {
    "role": "assistant",
    "content": "I don't have access to live weather data..."
  }
}
```

---

## `POST /debug/respond`

Run an LLM turn on an existing actor without a live call — useful for testing the inference binding.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `call_control_id` | `string` | **yes** | The Call Control ID whose actor should process the turn |

**Try it:**

```bash
curl -X POST https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/debug/respond \
  -H "Content-Type: application/json" \
  -d '{"call_control_id":"v3:abc123"}'
```

**Response `200`:**

```json
{
  "reply": "How can I help you today?"
}
```

---

## `GET /health/{liveness,readiness}`

Health check endpoints.

### Response `200`

```
ok
```

**Try it:**

```bash
curl https://edge-voice-agent-holds-call-<id>.telnyxcompute.com/health/liveness
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing fields or unexpected event |
| `404` | Unknown route |
| `500` | Server error — secrets not configured, or actor failure |
