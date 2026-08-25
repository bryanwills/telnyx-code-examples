# API Reference

This document defines the HTTP API contract for the AI-Powered Call Router Flask application.

## Endpoints

### `GET /health`

Simple health check endpoint used to verify the application is running.

**Request Body**

No request body required.

**Example Request**

```bash
curl -X GET http://localhost:5000/health
```

**Response Schema**

| Status Code | Schema |
|------------|--------|
| `200` | `{ "status": "string" }` |

**Example Response**

```json
{
  "status": "ok"
}
```

**Status Codes**

| Status Code | Description |
|------------|-------------|
| `200` | Service is healthy and reachable. |
| `500` | Internal server error. |

---

### `POST /webhook`

Telnyx Call Control webhook receiver. Handles inbound call events, gathers speech, classifies intent via the AI Inference API, and transfers the call based on the route table.

**Request Headers**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `telnyx-ed25519-signature` | string | Yes | Telnyx webhook signature for verification. |
| `telnyx-ed25519-timestamp` | string | Yes | Telnyx webhook timestamp for verification. |
| `Content-Type` | string | Yes | Must be `application/json`. |

**Request Body Schema**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | object | Yes | Telnyx event payload. |
| `data.event_type` | string | Yes | The type of call event (e.g., `call.initiated`, `call.answered`, `call.gather.ended`). |
| `data.payload` | object | Yes | The event payload containing call details. |
| `data.payload.call` | object | Yes | Call object containing metadata. |
| `data.payload.call.call_control_id` | string | Yes | Unique ID used to control the call. |
| `data.payload.call.direction` | string | Yes | Call direction (`incoming` or `outgoing`). |
| `data.payload.speech` | object | No | Present on `call.gather.ended`. Contains gathered speech data. |
| `data.payload.speech.result` | string | No | The transcribed text of the caller's speech. |

**Example Request**

```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -H "telnyx-ed25519-signature: $TELNYX_SIGNATURE" \
  -H "telnyx-ed25519-timestamp: $TELNYX_TIMESTAMP" \
  -d '{
    "data": {
      "event_type": "call.initiated",
      "payload": {
        "call": {
          "call_control_id": "v2:...",
          "direction": "incoming"
        }
      }
    }
  }'
```

**Response Schema**

| Status Code | Schema |
|------------|--------|
| `200` | `{ "status": "string" }` |
| `401` | `{ "error": "string" }` |

**Example Response**

```json
{
  "status": "ok"
}
```

**Status Codes**

| Status Code | Description |
|------------|-------------|
| `200` | Webhook received and processed successfully. |
| `401` | Webhook signature verification failed. |
| `500` | Internal server error. |
