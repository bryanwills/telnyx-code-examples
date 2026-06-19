# API Reference

Typed reference for the HTTP routes exposed by `server.js` and the Telnyx API endpoints it calls.

## HTTP Endpoints

### `POST /calls/initiate`

Initiates an outbound call from your Telnyx number.

#### Request

```json
{
  "to": "+12125551234",
  "message": "Hello from Telnyx!"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number (E.164, must start with `+`) |
| `message` | `string` | **yes** | Message text; presence is required to start the workflow |

#### Response `200`

```json
{
  "call_control_id": "v2:abc123...",
  "from": "+15551234567",
  "to": "+12125551234"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `call_control_id` | `string` | Identifier used for subsequent call control actions |
| `from` | `string` | Caller ID number used (`TELNYX_PHONE_NUMBER`) |
| `to` | `string` | Destination number that was dialed |

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/initiate \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234", "message": "Hello from Telnyx!"}'
```

---

### `POST /calls/:callControlId/speak`

Plays a text-to-speech message on an active call.

#### Path Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `callControlId` | `string` | **yes** | The `call_control_id` of an active call |

#### Request

```json
{
  "message": "Your appointment is confirmed.",
  "language": "en-US"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | `string` | **yes** | Text to synthesize and speak |
| `language` | `string` | no | TTS language code (defaults to `en-US`) |

#### Response `200`

```json
{
  "call_control_id": "v2:abc123...",
  "status": "ok"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `call_control_id` | `string` | Identifier of the call the TTS was issued on |
| `status` | `string` | Status returned by the Telnyx speak command |

**Try it:**

```bash
curl -X POST http://localhost:5000/calls/v2:abc123.../speak \
  -H "Content-Type: application/json" \
  -d '{"message": "Your appointment is confirmed.", "language": "en-US"}'
```

---

### `POST /webhooks/call`

Receives Call Control events from Telnyx. On `call.answered` the server auto-plays a TTS greeting; on `call.hangup` it logs the end of the call.

#### Request

```json
{
  "data": {
    "event_type": "call.answered",
    "call_control_id": "v2:abc123..."
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.event_type` | `string` | **yes** | Telnyx event type (e.g. `call.answered`, `call.hangup`) |
| `data.call_control_id` | `string` | **yes** | Identifier of the call the event belongs to |

#### Response `200`

```json
{
  "status": "received"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/call \
  -H "Content-Type: application/json" \
  -d '{"data": {"event_type": "call.answered", "call_control_id": "v2:abc123..."}}'
```

---

### `GET /health`

Health check for monitoring.

#### Response `200`

```json
{
  "status": "ok"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Telnyx API Endpoints Called

| SDK call | Method & path | Purpose |
|----------|---------------|---------|
| `client.calls.dial()` | `POST /v2/calls` | Initiate an outbound call ([reference](https://developers.telnyx.com/api-reference/call-commands/dial)) |
| `client.calls.actions.speak()` | `POST /v2/calls/{call_control_id}/actions/speak` | Play a TTS message on a call ([reference](https://developers.telnyx.com/api-reference/call-commands/speak-text)) |

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing fields or invalid phone format |
| `401` | Invalid API key |
| `429` | Rate limit exceeded |
| `503` | Network error connecting to Telnyx |
| `500` | Server / upstream API error |
