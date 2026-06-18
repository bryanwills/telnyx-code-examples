## `POST /conference/create`

Create conference endpoint.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conference_name` | `string` | **yes** | Conference name |
| `participants` | `array` | no | List of participant phone numbers |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/conference/create \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /conference/<conference_name>/add-participant`

Add participant endpoint.

### Request

```json
{
  "id": "abc-123",
  "status": "active",
  "created_at": "2026-06-18T21:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | Phone number |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/conference/example-id/add-participant \
  -H "Content-Type: application/json" \
  -d '{"id": "abc-123", "status": "active", "created_at": "2026-06-18T21:00:00Z"}'
```

---

## `POST /conference/<conference_name>/end`

End conference endpoint.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/conference/example-id/end \
  -H "Content-Type: application/json" \
  -d '{"error": "Invalid API key"}'
```

---

## `GET /conference/<conference_name>/status`

Get conference status endpoint.

### Response `200`

```json
{
  "error": "Resource not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/conference/example-id/status
```

---

## `POST /webhooks/call-events`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/call-events
```

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "healthy"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `active`, `answered`, `ended`, `hangup`, `healthy`, `initiated`, `received`

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
