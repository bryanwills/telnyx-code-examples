## `POST /webhooks/shopify/cart-abandoned`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/shopify/cart-abandoned
```

## `POST /recovery/run-sms`

Run sms recovery.

### Response `200`

```json
{"results": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/recovery/run-sms \
  -H "Content-Type: application/json" \
  -d '{"results": null}'
```

---

## `POST /recovery/run-calls`

Run call recovery.

### Response `200`

```json
{"results": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/recovery/run-calls \
  -H "Content-Type: application/json" \
  -d '{"results": null}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

### Events Handled

| Event | Action |
|-------|--------|
| `call.answered` | Begins interaction (TTS greeting or gather) |
| `call.speak.ended` | TTS finished — transitions to gather or next step |
| `call.gather.ended` | Input received — processes customer response |

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /carts`

List all carts.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/carts
```

---

## `POST /webhooks/shopify/order-created`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/shopify/order-created
```

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "results": []
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `call_initiated`, `ok`, `queued`, `sms_sent`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "results": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
