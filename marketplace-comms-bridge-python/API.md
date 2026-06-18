# API Reference — Marketplace Comms Bridge

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhooks/sms` | Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly. |
| `GET` | `/listings` | List listings. |
| `GET` | `/conversations` | List conversations. |
| `GET` | `/flagged` | List flagged. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /webhooks/sms`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

## `GET /listings`

List all listings.

### Response `200`

```json
{"listings": null}
```

---

## `GET /conversations`

List all conversations.

### Response `200`

```json
{"conversations": conversations[-50:]}
```

---

## `GET /flagged`

List all flagged.

### Response `200`

```json
{"flagged": null}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "conversations": "<string>",
  "flagged": "<string>"
}
```

---

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
