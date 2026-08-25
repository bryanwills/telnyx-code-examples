# API Reference — Network Incident Agent

This document describes the HTTP API contract for the `network-incident-agent` Flask application. All endpoints return JSON.

Base URL: `http://localhost:8080` (configurable via `PORT`)

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/inbound-sms` | Handle inbound SMS webhook from Telnyx |
| POST | `/webhook/call` | Handle inbound call webhook from Telnyx |
| GET | `/incident/status` | Get current incident state |
| POST | `/incident/update` | Update incident status and notify customers |
| POST | `/incident/notify` | Proactively notify all affected customers via SMS |
| POST | `/incident/rca` | Generate RCA document and upload to CloudFS |
| GET | `/health` | Health check |

---

## POST /webhooks/inbound-sms

Receives inbound SMS webhook events from Telnyx. Verifies the Ed25519 signature and logs the message.

### Request

The request body is the raw Telnyx webhook payload. The signature is passed in the `Telnyx-Signature-Ed25519` header.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Telnyx-Signature-Ed25519` | string | Yes | Ed25519 signature for webhook verification |
| `Content-Type` | string | Yes | `application/json` |

**Request Body Schema (Telnyx webhook payload):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.payload.from.phone_number` | string | Yes | Sender's phone number (E.164 format) |
| `data.payload.to[0].phone_number` | string | Yes | Recipient's phone number (E.164 format) |
| `data.payload.text` | string | Yes | Message body |
| `data.payload.id` | string | Yes | Unique message ID |
| `data.payload.direction` | string | Yes | `inbound` or `outbound` |
| `data.payload.message_type` | string | Yes | `SMS`, `MMS`, etc. |

### Example Request

```bash
curl -X POST http://localhost:8080/webhooks/inbound-sms \
  -H "Content-Type: application/json" \
  -H "Telnyx-Signature-Ed25519: <signature>" \
  -d '{
    "data": {
      "event_type": "message.received",
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "payload": {
        "id": "message-id-123",
        "direction": "inbound",
        "from": {
          "phone_number": "+1234567890"
        },
        "to": [
          {
            "phone_number": "+1987654321"
          }
        ],
        "text": "Is there an issue with my service?",
        "message_type": "SMS"
      }
    }
  }'
```

### Response

**200 OK**

```json
{
  "status": "ok"
}
```

**500 Internal Server Error**

```json
{
  "error": "Internal server error"
}
```

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Webhook processed successfully |
| 500 | Error processing webhook (signature verification failed, malformed payload, etc.) |

---

## `POST /webhook/call`

Receives inbound call webhook events from Telnyx. The agent answers with incident context.

### Request

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Telnyx-Signature-Ed25519` | string | Yes | Ed25519 signature for webhook verification |
| `Content-Type` | string | Yes | `application/json` |

**Request Body Schema (Telnyx webhook payload):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.payload.call_control_id` | string | Yes | Unique identifier for the call control session |
| `data.payload.from` | string | Yes | Caller's phone number (E.164 format) |
| `data.payload.to` | string | Yes | Called number (E.164 format) |
| `data.payload.call_leg_id` | string | Yes | Unique identifier for the call leg |
| `data.payload.call_session_id` | string | Yes | Unique identifier for the call session |

### Example Request

```bash
curl -X POST http://localhost:8080/webhook/call \
  -H "Content-Type: application/json" \
  -H "Telnyx-Signature-Ed25519: <signature>" \
  -d '{
    "data": {
      "event_type": "call.initiated",
      "id": "evt_123",
      "payload": {
        "call_control_id": "call-control-id-456",
        "call_leg_id": "call-leg-id-789",
        "call_session_id": "call-session-id-012",
        "from": "+1234567890",
        "to": "+1987654321"
      }
    }
  }'
```

### Response

**200 OK**

```json
{
  "status": "ok"
}
```

**500 Internal Server Error**

```json
{
  "error": "Internal server error"
}
```

### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Webhook processed successfully |
| 500 | Error processing webhook (signature verification failed, malformed payload, etc.) |

---

## `GET /incident/status`

Returns the current incident state, including status, severity, timeline, and affected services.

### Request

No request body or query parameters required.

### Example Request

```bash
curl http://localhost:8080/incident/status
```

### Response

**200 OK**

```json
{
  "status": "investigating",
  "severity": "SEV-1",
  "description": "",
  "affected_services": [],
  "start_time": "2025-01-15T10:30:00Z",
  "resolution_time": null,
  "root_cause": null,
  "timeline": [
    {
      "event_type": "incident_created",
      "description": "Incident agent initialized",
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ]
}
```

### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Incident state returned successfully |

---

## `POST /incident/update`

Updates the incident status and proactively notifies all affected customers via SMS.

### Request

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string | Yes | New incident status. Allowed values: `investigating`, `monitoring`, `resolved` |
| `description` | string | No | Optional description of the status change |

### Example Request

```bash
curl -X POST http://localhost:8080/incident/update \
  -H "Content-Type: application/json" \
  -d '{
    "status": "monitoring",
    "description": "Root cause identified, monitoring service recovery"
  }'
```

### Response

**200 OK**

```json
{
  "status": "updated",
  "incident_state": {
    "status": "monitoring",
    "severity": "SEV-1",
    "description": "",
    "affected_services": [],
    "start_time": "2025-01-15T10:30:00Z",
    "resolution_time": null,
    "root_cause": null,
    "timeline": [
      {
        "event_type": "incident_created",
        "description": "Incident agent initialized",
        "timestamp": "2025-01-15T10:30:00Z"
      },
      {
        "event_type": "status_update",
        "description": "Status changed to monitoring",
        "timestamp": "2025-01-15T10:45:00Z"
      },
      {
        "event_type": "customer_notification",
        "description": "Notified 3 customers via SMS",
        "timestamp": "2025-01-15T10:45:00Z"
      }
    ]
  }
}
```

**400 Bad Request**

```json
{
  "error": "Status is required"
}
```

### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Incident status updated and customers notified |
| 400 | Missing required `status` field in request body |
| 500 | Error updating incident status or sending SMS notifications |

---

## `POST /incident/notify`

Proactively sends an SMS message to all affected customers.

### Request

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | No | Custom message to send. Defaults to `Update on incident {incident_id}` |

### Example Request

```bash
curl -X POST http://localhost:8080/incident/notify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "We are aware of the issue and working on a fix. Estimated resolution: 2 hours."
  }'
```

### Response

**200 OK**

```json
{
  "status": "ok",
  "notified": 3
}
```

### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | SMS notifications sent successfully |
| 500 | Error sending SMS notifications |

---

## `POST /incident/rca`

Generates a Root Cause Analysis (RCA) document and uploads it to CloudFS.

### Request

**Request Body Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `root_cause` | string | Yes | Root cause description for the incident |

### Example Request

```bash
curl -X POST http://localhost:8080/incident/rca \
  -H "Content-Type: application/json" \
  -d '{
    "root_cause": "Network switch failure in us-east-1 due to hardware malfunction"
  }'
```

### Response

**200 OK**

```json
{
  "status": "ok"
}
```

**400 Bad Request**

```json
{
  "error": "Root cause is required"
}
```

### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | RCA document generated and uploaded to CloudFS |
| 400 | Missing required `root_cause` field in request body |
| 500 | Error generating RCA document or uploading to CloudFS |

---

## `GET /health`

Health check endpoint for the application.

### Request

No body or query parameters required.

### Example Request

```bash
curl http://localhost:8080/health
```

### Response

**200 OK**

```json
{
  "status": "healthy"
}
```

### Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Application is running and healthy |

---

## Common Error Responses

All endpoints return errors in the following format:

```json
{
  "error": "Error message"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid request body or missing required fields |
| 404 | Endpoint not found |
| 500 | Internal server error (details logged, not exposed to client) |
