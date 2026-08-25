# API Reference

The `shipment-agent` Flask application exposes the following HTTP endpoints for managing shipment entities, receiving carrier updates, handling Telnyx webhooks, and triggering AI interactions.

## Endpoints

### 1. Health Check

Simple health probe for the application.

**Request**

`GET /health`

**Example Request**

```bash
curl -X GET http://localhost:5000/health
```

**Response**

| Status Code | Description | JSON Shape |
| :--- | :--- | :--- |
| 200 | OK | `{"status": "string"}` |

**Example Response (200 OK)**

```json
{
  "status": "ok"
}
```

---

### 2. Get Agent State

Retrieves the current state, history, and scheduled wakes for a specific shipment agent.

**Request**

`GET /api/agents/<shipment_id>`

**Path Parameters**

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `shipment_id` | string | Yes | The unique identifier for the shipment (e.g., `SHP-12345`). |

**Example Request**

```bash
curl -X GET http://localhost:5000/api/agents/SHP-12345
```

**Response**

| Status Code | Description | JSON Shape |
| :--- | :--- | :--- | :--- |
| 200 | OK | `AgentState` |
| 404 | Not Found | `{"error": "string"}` |
| 500 | Internal Server Error | `{"error": "string"}` |

**Example Response (200 OK)**

```json
{
  "shipment_id": "SHP-12345",
  "status": "IN_TRANSIT",
  "eta": "2023-11-08",
  "carrier": "FedEx",
  "history": [
    {
      "timestamp": "2023-11-05T14:30:00+00:00",
      "event": "PICKED_UP",
      "data": {}
    }
  ],
  "scheduled_wakes": [
    {
      "wake_at": "2023-11-12T14:30:00+00:00",
      "event": "FEEDBACK_REQUEST"
    }
  ]
}
```

---

### 3. Trigger Agent Call

Simulates a customer calling the shipment agent. The agent responds with full shipment context via Call Control.

**Request**

`POST /api/agents/<shipment_id>/call`

**Path Parameters**

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `shipment_id` | string | Yes | The unique identifier for the shipment. |

**Request Body**

No request body required.

**Example Request**

```bash
curl -X POST http://localhost:5000/api/agents/SHP-12345/call
```

**Response**

| Status Code | Description | JSON Shape |
| :--- | :--- | :--- | :--- |
| 200 | OK | `{"shipment_id": "string", "response": "string"}` |
| 500 | Internal Server Error | `{"error": "string"}` |

**Example Response (200 OK)**

```json
{
  "shipment_id": "SHP-12345",
  "response": "Hello! I'm your shipment agent for SHP-12345. Current status: {\"shipment_id\": \"SHP-12345\", \"status\": \"IN_TRANSIT\", ...}. How can I help?"
}
```

---

### 4. Carrier Webhook

Handles inbound carrier status updates (e.g., FedEx/UPS API). Wakes the corresponding shipment agent to process the event and proactively notify the customer.

**Request**

`POST /webhooks/carrier`

**Request Body Schema**

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `shipment_id` | string | Yes | The unique identifier for the shipment. |
| `status` | string | Yes | The new carrier status. Accepted values: `PICKED_UP`, `IN_TRANSIT`, `DELAYED`, `OUT_FOR_DELIVERY`, `DELIVERED`. |
| `event_data` | object | No | Additional data related to the event (e.g., `{"new_eta": "2023-11-10"}`). |

**Example Request**

```bash
curl -X POST http://localhost:5000/webhooks/carrier \
  -H "Content-Type: application/json" \
  -d '{
    "shipment_id": "SHP-12345",
    "status": "DELAYED",
    "event_data": {
      "new_eta": "2023-11-10"
    }
  }'
```

**Response**

| Status Code | Description | JSON Shape |
| :--- | :--- | :--- | :--- |
| 200 | OK | `{"status": "string"}` |
| 400 | Bad Request | `{"error": "string"}` |
| 500 | Internal Server Error | `{"error": "string"}` |

**Example Response (200 OK)**

```json
{
  "status": "ok"
}
```

---

### 5. Telnyx Webhook

Handles inbound Telnyx webhooks for SMS replies and Call Control events. Verifies the Telnyx Ed25519 signature.

**Request**

`POST /webhooks/telnyx`

**Headers**

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Telnyx-Signature-Ed25519` | string | Yes | The Ed25519 signature from Telnyx. |
| `Telnyx-Signature-Timestamp` | string | Yes | The timestamp from Telnyx. |

**Request Body Schema**

The request body is the raw Telnyx event payload. The application reads `data.event_type` and `data.payload` to route the event.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `data.event_type` | string | Yes | The type of Telnyx event (e.g., `message.received`, `call.initiated`). |
| `data.payload` | object | Yes | The event payload containing message or call details. |

**Example Request**

```bash
curl -X POST http://localhost:5000/webhooks/telnyx \
  -H "Content-Type: application/json" \
  -H "Telnyx-Signature-Ed25519: your_signature" \
  -H "Telnyx-Signature-Timestamp: 1699200000" \
  -d '{
    "data": {
      "event_type": "message.received",
      "payload": {
        "from": {"phone_number": "+1234567890"},
        "to": {"phone_number": "+1987654321"},
        "text": "Where is my package?"
      }
    }
  }'
```

**Response**

| Status Code | Description | JSON Shape |
| :--- | :--- | :--- | :--- |
| 200 | OK | `{"status": "string"}` |
| 401 | Unauthorized | `{"error": "string"}` |
| 500 | Internal Server Error | `{"error": "string"}` |

**Example Response (200 OK)**

```json
{
  "status": "ok"
}
```
