## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /leaderboard`

Leaderboard.

### Response `200`

```json
{"leaderboard": null}
```

**Try it:**

```bash
curl http://localhost:5000/leaderboard
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `game_over`, `ignored`, `ok`, `playing`, `started`, `timeout`, `won`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "leaderboard": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
