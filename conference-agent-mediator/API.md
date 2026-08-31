# API Reference — Conference Agent Mediator

This document defines the HTTP and WebSocket API contract for the `conference-agent-mediator` Edge application.

## Base URL

```
https://<your-edge-subdomain>.telnyx.io
```

## Authentication

All endpoints require a valid `TELNYX_API_KEY` passed in the `Authorization` header as a Bearer token.

```
Authorization: Bearer <TELNYX_API_KEY>
```

---

## REST Endpoints

### 1. Start Conference & Agent

Initiates a Call Control conference, provisions a WebSocket endpoint for observers, and triggers the `ConferenceAgent` to join the bridge.

**Endpoint:** `POST /api/conferences`

#### Request Body Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conference_name` | string | Yes | Unique name for the conference bridge. |
| `phone_numbers` | string[] | No | E.164 phone numbers to dial into the conference. |
| `observer_webhook_url` | string | No | URL to receive post-conference summary webhooks. |

#### Example Request

```bash
curl -X POST https://<your-edge-subdomain>.telnyx.io/api/conferences \
  -H "Authorization: Bearer $TELNYX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conference_name": "standup-sync-831",
    "phone_numbers": ["+15551234567", "+15557654321"],
    "observer_webhook_url": "https://example.com/webhooks/summary"
  }'
```

#### Response Schema

**201 Created**
```json
{
  "conference_id": "conf_3f8a...",
  "conference_name": "standup-sync-831",
  "websocket_url": "wss://<your-edge-subdomain>.telnyx.io/ws/transcript/conf_3f8a...",
  "status": "initiated"
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 201 | Conference successfully initiated and Agent is joining. |
| 400 | Bad Request. Missing required fields or invalid phone number format. |
| 401 | Unauthorized. Missing or invalid `TELNYX_API_KEY`. |
| 500 | Internal Server Error. Failed to provision Call Control conference. |

---

### 2. Get Conference Summary

Retrieves the transcript, turn-taking metrics, and LLM-generated summary for a completed or active conference.

**Endpoint:** `GET /api/conferences/:conference_id/summary`

#### Path Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conference_id` | string | Yes | The ID of the conference returned by the creation endpoint. |

#### Example Request

```bash
curl -X GET https://<your-edge-subdomain>.telnyx.io/api/conferences/conf_3f8a.../summary \
  -H "Authorization: Bearer $TELNYX_API_KEY"
```

#### Response Schema

**200 OK**
```json
{
  "conference_id": "conf_3f8a...",
  "status": "completed",
  "participants": 3,
  "duration_seconds": 1840,
  "turn_taking_metrics": {
    "imbalances_detected": true,
    "silent_participants": ["+15557654321"]
  },
  "summary": "The team discussed the Sprint 3 deliverables. Alice committed to finishing the API docs. Bob was prompted to share his update on the UI components."
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK. Summary retrieved successfully. |
| 401 | Unauthorized. Missing or invalid `TELNYX_API_KEY`. |
| 404 | Not Found. Conference ID does not exist or has been purged. |
| 500 | Internal Server Error. Failed to fetch summary from state. |

---

### 3. Telnyx Webhook Receiver

Receives Call Control webhooks from Telnyx to track conference state, participant join/leave events, and trigger the post-conference summary + SMS workflow.

**Endpoint:** `POST /webhooks/telnyx`

#### Request Body Schema

Telnyx Call Control Webhook payload (varies by event). 

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.event_type` | string | Yes | The type of Call Control event (e.g., `conference.participant.joined`, `conference.ended`). |
| `data.payload.conference_id` | string | Yes | The Telnyx conference ID. |
| `data.payload.call_control_id` | string | Yes | The Call Control ID of the participant. |

#### Example Request

```bash
curl -X POST https://<your-edge-subdomain>.telnyx.io/webhooks/telnyx \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "event_type": "conference.ended",
      "payload": {
        "conference_id": "conf_3f8a...",
        "call_control_id": "call_..."
      }
    }
  }'
```

#### Response Schema

**200 OK**
```json
{
  "status": "received"
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK. Webhook received and signature verified. |
| 400 | Bad Request. Invalid payload or failed Ed25519 signature verification. |
| 500 | Internal Server Error. Failed to process webhook event. |

---

## WebSocket Endpoints

### 1. Live Transcript Stream

Provides a real-time stream of Speech-to-Text (STT) transcription and Agent mediation events for UI observers.

**Endpoint:** `GET /ws/transcript/:conference_id`

#### Connection Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conference_id` | string | Yes | The ID of the conference to observe. |

#### Message Schemas (Server → Client)

**Transcription Event**
```json
{
  "type": "transcript",
  "participant": "+15551234567",
  "text": "I'll have the API docs done by EOD.",
  "timestamp": 1698765432100
}
```

**Agent Mediation Event**
```json
{
  "type": "agent_prompt",
  "text": "Bob, we haven't heard from you on the UI components. Any updates?",
  "timestamp": 1698765439800
}
```

#### Status Codes

| Status Code | Description |
|-------------|-------------|
| 101 | Switching Protocols. WebSocket connection established. |
| 401 | Unauthorized. Missing or invalid `TELNYX_API_KEY` in connection headers. |
| 404 | Not Found. Conference ID does not exist or agent is not active. |
