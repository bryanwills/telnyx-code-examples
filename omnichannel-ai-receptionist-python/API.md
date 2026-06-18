## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /customers`

List all customers.

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl http://localhost:5000/customers
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "No payload"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `call_ended`, `event_received`, `greeting`, `ignored`, `listening`, `ok`, `reprompting`, `responded`, `responding`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "No payload"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
