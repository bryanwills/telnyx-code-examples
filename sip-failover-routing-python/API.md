# API Reference — Production-ready SIP failover routing system with Flask and Telnyx.

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sip/connections` | List connections. |
| `POST` | `/sip/connections` | Create a new connection. |
| `GET` | `/sip/connections/<connection_id>` | Get connection. |
| `GET` | `/sip/health` | Health check and service status. |
| `GET` | `/sip/failover-status` | Failover status. |
| `POST` | `/webhooks/call` | Receives Telnyx webhook events. |
| `POST` | `/sip/assign-number` | Assign number. |

---

## `GET /sip/connections`

List all connections.

### Response `200`

```json
{"connections": null}
```

---

## `POST /sip/connections`

Create a new connection.

### Request

```json
{
  "name": "Jane Smith"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |

### Response `200`

```json
{
  "connections": []
}
```

---

## `GET /sip/connections/<connection_id>`

Get a specific connection by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /sip/health`

Health check and service status.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

---

## `GET /sip/failover-status`

Failover status.

### Response `200`

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

---

## `POST /webhooks/call`

Receives Telnyx webhook events.

---

## `POST /sip/assign-number`

Assign number.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | Phone number |
| `connection_id` | `string` | **yes** | Connection id |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
