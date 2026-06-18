## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /bookings`

List all bookings.

### Response `200`

```json
{"bookings": null}
```

**Try it:**

```bash
curl http://localhost:5000/bookings
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "bookings": "<string>",
  "available": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `booked`, `ignored`, `no_slots`, `ok`, `processing`, `showing_slots`

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
