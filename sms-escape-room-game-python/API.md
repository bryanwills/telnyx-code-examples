# API Reference — SMS Escape Room Game

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/messaging` | Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly. |
| `GET` | `/leaderboard` | Leaderboard. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

## `GET /leaderboard`

Leaderboard.

### Response `200`

```json
{"leaderboard": null}
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
