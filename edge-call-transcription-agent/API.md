## `POST /webhooks/voice`

Receives Telnyx Call Control webhooks and drives the transcription pipeline.

### Events Handled

#### `call.initiated`

Answers the inbound call and records the start in a per-call actor.

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

Speaks a short greeting via Call Control TTS so the caller knows their speech is being transcribed.

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

When the greeting finishes, starts streaming transcription (Telnyx engine, inbound track only).

| Field | Type | Description |
|-------|------|-------------|
| `data.payload.call_control_id` | `string` | Call ID |
| `data.payload.client_state` | `string` | Base64-encoded `{ speak_stage: "greeting" }` |

**Response `200`:**

```json
{
  "action": "transcribing"
}
```

---

#### `call.transcription`

Appends a transcript fragment to durable agent state. Interim fragments (`is_final=false`) are kept in `state.segments` for the live dashboard; final fragments (`is_final=true`) accumulate into `state.transcriptText` (what gets summarized).

| Field | Type | Description |
|-------|------|-------------|
| `data.payload.call_control_id` | `string` | Call ID |
| `data.payload.transcription_data.transcript` | `string` | The transcribed text fragment |
| `data.payload.transcription_data.is_final` | `boolean` | Whether this is a final (not interim) result |

**Response `200`:**

```json
{
  "action": "transcript_final",
  "turn": "Hi, I'm calling about the invoice from last week"
}
```

or

```json
{
  "action": "transcript_interim",
  "turn": "Hi, I'm calling about"
}
```

---

#### `call.hangup`

Stops transcription and queues the non-blocking finalize pipeline on the actor (`summarize` → `store` → `notify`). Returns immediately; the LLM summary, SQL persist, and SMS send happen asynchronously inside the actor.

**Response `200`:**

```json
{
  "action": "finalizing"
}
```

---

## `GET /transcripts`

List recent stored transcripts across all calls, most recent first. Reads from the shared `TranscriptRegistry` actor (single "global" instance) that each per-call `TranscribeAgent` upserts into on hangup.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | `number` | no | Max rows to return (default `50`, max `200`) |

**Try it:**

```bash
curl https://edge-call-transcription-agent-<id>.telnyxcompute.com/transcripts?limit=50
```

**Response `200`:**

```json
{
  "transcripts": [
    {
      "call_control_id": "v3:550e8400-e29b-41d4-a716-446655440000",
      "from_number": "+17177247292",
      "to_number": "+16282564655",
      "transcript": "Hi, I'm calling about the invoice from last week. The amount seems wrong.",
      "summary": "Caller asked about an invoice from last week with a possibly incorrect amount. Wants a callback to discuss.",
      "started_at": 1724359200000,
      "ended_at": 1724359260000,
      "turn_count": 2,
      "status": "stored"
    }
  ]
}
```

---

## `GET /transcripts/:call_control_id`

Fetch a single stored transcript + summary.

### Path Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `call_control_id` | `string` | **yes** | The Call Control ID of the call to fetch |

**Try it:**

```bash
curl https://edge-call-transcription-agent-<id>.telnyxcompute.com/transcripts/v3:550e8400-e29b-41d4-a716-446655440000
```

**Response `200`:**

```json
{
  "call_control_id": "v3:550e8400-e29b-41d4-a716-446655440000",
  "from_number": "+17177247292",
  "to_number": "+16282564655",
  "transcript": "Hi, I'm calling about the invoice from last week...",
  "summary": "John called about an invoice from last week. He wants a callback to discuss it.",
  "started_at": 1724359200000,
  "ended_at": 1724359260000,
  "turn_count": 2,
  "status": "stored"
}
```

**Response `404`** — transcript not found (call hasn't hung up yet, or call_control_id is wrong):

```json
{
  "error": "transcript not found"
}
```

---

## `GET /debug/state`

Inspect the live actor state for a call — phase, accumulated segments, transcriptText, summary, error. Useful while a call is in progress or right after hangup to see the actor's pipeline progress.

### Query Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `call_control_id` | `string` | **yes** | The Call Control ID of the call to inspect |

**Try it:**

```bash
curl "https://edge-call-transcription-agent-<id>.telnyxcompute.com/debug/state?call_control_id=v3:abc123"
```

**Response `200`:**

```json
{
  "callControlId": "v3:abc123",
  "from": "+17177247292",
  "to": "+16282564655",
  "phase": "transcribing",
  "segments": [
    { "text": "Hi, I'm calling", "at": 1724359201000, "isFinal": false },
    { "text": "Hi, I'm calling about the invoice from last week", "at": 1724359203000, "isFinal": true }
  ],
  "transcriptText": "Hi, I'm calling about the invoice from last week",
  "summary": "",
  "startedAt": 1724359200000,
  "endedAt": 0,
  "turnCount": 1,
  "error": ""
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
curl https://edge-call-transcription-agent-<id>.telnyxcompute.com/health/liveness
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing `call_control_id` or unexpected event |
| `404` | Unknown route or transcript not found |
| `500` | Server error — secrets not configured, or actor failure |
| `502` | Upstream Telnyx API call failed (answer, speak, transcription_start) |
