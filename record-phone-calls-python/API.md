## `POST /calls/initiate`

Initiate call endpoint.

### Request

```json
{
  "to": "+12125559999"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number (E.164) |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/initiate \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125559999"}'
```

---

## `POST /calls/<call_control_id>/recording/start`

Start recording endpoint.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/example-id/recording/start \
  -H "Content-Type: application/json" \
  -d '{"error": "Invalid API key"}'
```

---

## `POST /calls/<call_control_id>/recording/stop`

Stop recording endpoint.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/example-id/recording/stop \
  -H "Content-Type: application/json" \
  -d '{"error": "Invalid API key"}'
```

---

## `POST /calls/<call_control_id>/hangup`

Hangup endpoint.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/example-id/hangup \
  -H "Content-Type: application/json" \
  -d '{"error": "Invalid API key"}'
```

---

## `POST /webhooks/call-events`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/call-events
```

## `GET /calls/<call_control_id>/status`

Get call status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/calls/example-id/status
```

---

## Status Values

Records use these status values: `answered`, `hangup`, `hangup_requested`, `initiated`, `received`, `recording`, `recording_stopped`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Call not found"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
