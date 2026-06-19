# API Reference -- Edge Fraud Firewall

Base URL: `http://localhost:5000`

## All Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhooks/voice` | Voice |
| `GET` | `/blocklist` | Blocklist |
| `POST` | `/blocklist` | Blocklist |
| `GET` | `/stats` | Stats |
| `GET` | `/health` | Health |

---

## `POST /webhooks/voice`

Telnyx webhook handler.

### Events Handled

| Event | Description |
|-------|-------------|
| `call.initiated` | New inbound or outbound call detected |
| `call.answered` | Call connected, app begins interaction with greeting |
| `call.speak.ended` | TTS playback finished, transitions to next action |
| `call.hangup` | Call ended, cleans up session state and logs outcome |

### Response `200`

```json
{"status": "ok"}
```

---

## `GET /blocklist`

Blocklist.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/blocklist
```

---

## `POST /blocklist`

Blocklist.

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
curl -X POST http://localhost:5000/blocklist \
  -H "Content-Type: application/json" \
  -d '{"example": "value"}'
```

---

## `GET /stats`

Stats.

### Response `200`

```json
{"status": "ok"}
```

### Try it

```bash
curl http://localhost:5000/stats
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
