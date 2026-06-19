# API Reference -- Edge Number Masking

Base URL: `http://localhost:5000`

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/pool` | Pool |
| `POST` | `/bookings` | Bookings |
| `DELETE` | `/bookings/<booking_id>` | <Booking Id> |
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/bookings` | Bookings |
| `GET` | `/health` | Health |

---

## `POST /pool`

Pool.

### Request

```json
{"example": "value"}
```

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl -X POST http://localhost:5000/pool \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

---

## `POST /bookings`

Bookings.

### Request

```json
{"example": "value"}
```

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl -X POST http://localhost:5000/bookings \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

---

## `DELETE /bookings/<booking_id>`

<Booking Id>.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/bookings/<booking_id>
```

---

## `POST /webhooks/voice`

Telnyx webhook handler.

### Events Handled

| Event | Description |
|-------|-------------|
| `call.initiated` | New inbound or outbound call detected |
| `call.answered` | Call connected, app begins interaction with greeting |
| `call.recording.saved` | Recording available for download |
| `call.hangup` | Call ended, cleans up session state and logs outcome |

### Response `200`

```json
{"status": "ok"}
```

---

## `GET /bookings`

Bookings.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/bookings
```

---

## `GET /health`

Health.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/health
```

---

## Error Handling

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|--------|
| `200` | Success |
| `400` | Bad request |
| `404` | Not found |
| `500` | Server error |
