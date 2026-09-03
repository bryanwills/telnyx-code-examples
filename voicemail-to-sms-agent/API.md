# API Reference — `voicemail-to-sms-agent`

This document defines the HTTP API contract for the Voicemail-to-SMS Agent Telnyx Edge application.

## Base URL

All endpoints are relative to your deployed Edge function base URL (e.g., `https://<func-id>.telnyxcompute.com`).

## Authentication

The webhook endpoint verifies the Telnyx Ed25519 signature header (`Telnyx-Signature-Ed25519`) and timestamp (`Telnyx-Timestamp`) on every inbound request using the `TELNYX_PUBLIC_KEY` env var. When the public key is not configured, verification is skipped in demo mode (`LIVE_MODE=false`) and unverified requests are rejected in live mode.

## Endpoints

### 1. Telnyx Webhook Receiver

Receives Telnyx webhooks (e.g., `call.recording.saved` after a voicemail is left). Triggers the `VoicemailAgent` to download the recording, transcribe it, summarize it via LLM, send an SMS to the mailbox owner, and archive the audio to Cloud Storage.

**Endpoint:** `POST /webhook`

#### Request Body Schema

The endpoint expects a standard Telnyx webhook payload.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `event` | `string` | No | The event type (e.g., `call.recording.saved`). Informational — the agent processes any payload carrying recording metadata. |
| `data.payload.call_control_id` | `string` | Yes | Unique identifier for the Call Control session. |
| `data.payload.from` | `string` | No | The caller's phone number (included in the SMS summary). |
| `data.payload.recording_url` | `string` | Conditional | Direct URL to the voicemail audio. Preferred when present. |
| `data.payload.recording_id` | `string` | Conditional | Recording ID — resolved via `GET /v2/recordings/{id}` when `recording_url` is absent. |

Either `recording_url` or `recording_id` must be present.

#### Example Request

```bash
curl -X POST https://<func-id>.telnyxcompute.com/webhook \
  -H "Content-Type: application/json" \
  -H "Telnyx-Signature-Ed25519: <signature>" \
  -H "Telnyx-Timestamp: <timestamp>" \
  -d '{
    "event": "call.recording.saved",
    "data": {
      "payload": {
        "call_control_id": "v2:...",
        "from": "+15559876543",
        "recording_id": "rec-abc-123",
        "recording_url": "https://storage.telnyx.com/..."
      }
    }
  }'
```

#### Response Schema

```json
{
  "status": "success",
  "recording_id": "rec-abc-123",
  "summary": "John called about tomorrow's 3pm meeting, asked you to confirm.",
  "sms_sent": false,
  "archived": false
}
```

`sms_sent` and `archived` are `false` in demo mode (`LIVE_MODE=false`); the SMS payload is logged instead.

#### Status Codes

| Status Code | Description |
| :--- | :--- |
| **200** | `OK` - Voicemail processed successfully. |
| **400** | `Bad Request` - Malformed JSON body. |
| **401** | `Unauthorized` - Signature verification failed (or public key missing in live mode). |
| **500** | `Internal Server Error` - Processing failed (details logged server-side, not returned). |

---

### 2. List Processed Voicemails

Returns the most recent voicemails processed by the agent (persisted in actor storage, capped at 100).

**Endpoint:** `GET /voicemails`

#### Example Request

```bash
curl -X GET https://<func-id>.telnyxcompute.com/voicemails
```

#### Response Schema

```json
{
  "voicemails": [
    {
      "recording_id": "rec-abc-123",
      "caller": "+15559876543",
      "transcript_preview": "Hi, it's John. I wanted to confirm tomorrow's meeting...",
      "summary": "John called about tomorrow's 3pm meeting, asked you to confirm.",
      "sms_sent": true,
      "archived": true,
      "processed_at": "2026-09-02T16:45:00.000Z"
    }
  ]
}
```

#### Status Codes

| Status Code | Description |
| :--- | :--- |
| **200** | `OK` - Returns the list (possibly empty). |

---

### 3. Agent Stats

Returns aggregate counters for processed voicemails.

**Endpoint:** `GET /stats`

#### Example Request

```bash
curl -X GET https://<func-id>.telnyxcompute.com/stats
```

#### Response Schema

```json
{
  "total_voicemails": 12,
  "sms_sent": 10,
  "archived": 9
}
```

#### Status Codes

| Status Code | Description |
| :--- | :--- |
| **200** | `OK` - Returns the counters. |

---

### 4. Debug Events

Returns the last 20 recorded runtime events (webhook events, Call Control action results, pipeline steps and failures). Useful for diagnosing webhook/flow issues without access to function logs.

**Endpoint:** `GET /debug/events`

#### Example Request

```bash
curl -X GET https://<func-id>.telnyxcompute.com/debug/events
```

#### Response Schema

```json
{
  "events": [
    { "ts": "2026-09-03T00:56:21.876Z", "step": "sms_sent", "to": "+15551234567" },
    { "ts": "2026-09-03T00:56:03.647Z", "event": "call.recording.saved" },
    { "ts": "2026-09-03T00:55:40.000Z", "action": "record_start", "ok": true }
  ]
}
```

#### Status Codes

| Status Code | Description |
| :--- | :--- |
| **200** | `OK` - Returns the event list (possibly empty). |

---

### 5. Health Checks

Liveness/readiness probes for the Edge function.

**Endpoints:** `GET /health/liveness` and `GET /health/readiness`

#### Example Request

```bash
curl -X GET https://<func-id>.telnyxcompute.com/health/liveness
```

#### Response

Plain-text `ok` with HTTP 200.

## Behavior Notes

- **Duplicate suppression** — a dual-channel call produces multiple `call.recording.saved` webhooks (one per recording file). The agent dedupes by `recording_id` and by `call_session_id`, so one call produces at most one SMS.
- **Caller enrichment** — `call.recording.saved` payloads may omit the caller number; the agent falls back to the `from` captured at `call.initiated`.
- **Archiving is best-effort** — if the Cloud Storage binding/bucket is unavailable, processing continues (`archived: false`) and the failure is logged to `/debug/events`.
