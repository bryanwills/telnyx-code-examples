## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /devices`

List all devices.

### Response `200`

```json
{"devices": DEVICES}
```

**Try it:**

```bash
curl http://localhost:5000/devices
```

---

## `GET /commands`

List all commands.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/commands
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "devices": "<string>",
  "commands": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `active`, `answering`, `closed`, `ended`, `executed`, `greeting`, `listening`, `ok`, `on`, `recording`, `reprompting`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "devices": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
