# API Reference

This document describes the HTTP endpoints exposed by the AI Call Campaign Orchestrator. All endpoints return JSON.

## Base URL

When running locally, the base URL is `http://localhost:5000` (or the value of the `PORT` environment variable).

---

## `POST /campaign`

Creates a new outbound call campaign. This endpoint accepts a list of phone numbers, queues them for calling, and starts the rate-limited scheduler.

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_numbers` | `array[string]` | Yes | List of E.164-formatted phone numbers to call (e.g., `+15551234567`). Must be a non-empty array. |

### Example Request

```bash
curl -X POST http://localhost:5000/campaign \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": [
      "+15551234567",
      "+15557654321",
      "+15559876543"
    ]
  }'
```

### Response

#### `202 Accepted`

```json
{
  "campaign_id": "3f2c1a5e-8b7d-4e6f-9a0c-1d2e3f4a5b6c",
  "status": "started"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `campaign_id` | `string` | UUID identifying the campaign. Use this to poll campaign status. |
| `status` | `string` | Always `"started"` on success. |

#### `400 Bad Request`

Returned when the request body is missing or invalid.

```json
{
  "error": "phone_numbers is required"
}
```

or

```json
{
  "error": "phone_numbers must be a non-empty list"
}
```

---

## `GET /campaign/<campaign_id>`

Retrieves the status and results of a campaign.

### Path Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `campaign_id` | string | Yes | The UUID returned from `POST /campaign`. |

### Example Request

```bash
curl http://localhost:5000/campaign/2f9c1a5e-8b7d-4e6f-9c0c-1d2e3f4a5b6c
```

### Response

**200 OK**

```json
{
  "campaign_id": "2f9c1a5e-8b7d-4e6f-9c0c-1d2e3f4a5b6c",
  "total": 3,
  "completed": false,
  "results": [
    {
      "to": "+15551234567",
      "status": "queued",
      "call_control_id": "cctl_1a2b3c4d5e6f7a8b9c0d1e2f"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `campaign_id` | string | The campaign's unique identifier. |
| `total` | integer | Total number of phone numbers in the campaign. |
| `completed` | boolean | `true` when all calls have been processed and the SMS summary has been sent. |
| `results` | array | List of call results. Each result contains `to`, `status`, and optionally `call_control_id` or `error`. |

#### `404 Not Found`

Returned when the campaign ID does not exist.

```json
{
  "error": "Campaign not found"
}
```

---

## `POST /webhooks/call`

Receives Call Control webhook events from Telnyx (e.g., call answered, call hangup). This endpoint verifies the Telnyx Ed25519 signature before processing.

### Request Body

The raw request body is the Telnyx webhook payload. The signature is verified using the `TELNYX_PUBLIC_KEY` environment variable.

### Example Request

```bash
curl -X POST http://localhost:5000/webhooks/call \
  -H "Content-Type: application/json" \
  -H "Telnyx-Signature-Ed25519: <signature>" \
  -H "Telnyx-Timestamp: <timestamp>" \
  -d '{
    "data": {
      "event_type": "call.initiated",
      "payload": {
        "call_control_id": "cctl_1a2b3c4d5e6f7a8b9c0d1e2f",
        "call_leg_id": "leg_1a2b3c4d5e6f7a8b9c0d1e2f",
        "call_session_id": "sess_1a2b3c4d5e6f7a8b9c0d1e2f",
        "from": "+15551234567",
        "to": "+15557654321"
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

#### `403 Forbidden`

Returned when the Ed25519 signature verification fails.

```json
{
  "error": "Invalid signature"
}
```

---

## `GET /health`

Health check endpoint.

### Example Request

```bash
curl http://localhost:5000/health
```

### Response

**200 OK**

```json
{
  "status": "ok"
}
```

---

## Status Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Request succeeded. |
| `202` | Campaign creation accepted and processing started. |
| `400` | Invalid request body (missing or malformed fields). |
| `403` | Webhook signature verification failed. |
| `404` | Campaign ID not found. |
| `500` | Internal server error. The response body will contain a generic error message; details are logged server-side. |
