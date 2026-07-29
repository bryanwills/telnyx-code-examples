## `POST /voicemails/transcript`

Classify a voicemail transcript and determine routing.

### Request

```json
{
  "transcript": "This is an emergency. Our system is down.",
  "caller_number": "+17177247292"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript` | `string` | **yes** | The voicemail transcript (max 6000 chars) |
| `caller_number` | `string` | no | Caller's phone number (E.164) |

### Response `201`

```json
{
  "id": "vm-1750280400",
  "transcript": "...",
  "category": "urgent",
  "confidence": 1.0,
  "priority": "high",
  "reason": "...",
  "suggested_action": "...",
  "route": "slack",
  "routed_to": "#oncall-alerts",
  "routing_status": "delivered",
  "caller_number": "+17177247292",
  "model_used": "zai-org/GLM-5.2",
  "generated_at": "2026-07-29T12:23:52Z"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/voicemails/transcript \
  -H "Content-Type: application/json" \
  -d '{"transcript":"I have a billing question about my invoice"}'
```

---

## `POST /voicemails/process`

Upload a voicemail audio file → STT → classify → route.

### Request (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `file` | **yes** | Audio file (WAV, MP3) |
| `caller_number` | `string` | no | Caller's phone number |

### Response `201`

```json
{
  "id": "vm-1750280401",
  "transcript": "...",
  "category": "support",
  "route": "ticket",
  "routed_to": "support-queue",
  "routing_status": "queued",
  "source": "audio:voicemail.wav",
  "generated_at": "..."
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/voicemails/process \
  -F "file=@voicemail.wav"
```

---

## `GET /voicemails`

List all processed voicemails (most recent 50).

### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `category` | `string` | Filter by category (urgent, billing, support, sales, spam, routine) |

### Response `200`

```json
{
  "voicemails": [
    {
      "id": "vm-1750280400",
      "category": "urgent",
      "route": "slack",
      "routing_status": "delivered",
      "priority": "high",
      "generated_at": "..."
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/voicemails
curl "http://localhost:5000/voicemails?category=spam"
```

---

## `GET /voicemails/<id>`

Fetch a specific voicemail with routing decision.

### Response `200`

```json
{
  "id": "vm-1750280400",
  "transcript": "...",
  "category": "urgent",
  "confidence": 1.0,
  "route": "slack",
  "routed_to": "#oncall-alerts"
}
```

### Response `404`

```json
{"error": "voicemail not found"}
```

**Try it:**

```bash
curl http://localhost:5000/voicemails/vm-1750280400
```

---

## `GET /routes`

List all routing decisions.

### Response `200`

```json
{
  "routes": [
    {
      "id": "vm-1750280400",
      "category": "urgent",
      "route": "slack",
      "routed_to": "#oncall-alerts",
      "routing_status": "delivered",
      "priority": "high",
      "generated_at": "..."
    }
  ]
}
```

**Try it:**

```bash
curl http://localhost:5000/routes
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "voicemails": 0,
  "primary_model": "zai-org/GLM-5.2",
  "fallback_model": "meta-llama/Llama-3.3-70B-Instruct",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `201` | Voicemail processed |
| `400` | Bad request — missing transcript or file |
| `404` | Voicemail not found |
| `422` | Transcription returned empty text |
| `500` | Server error |
