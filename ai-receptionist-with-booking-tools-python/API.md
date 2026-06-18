# API Reference — AI Receptionist with Booking Tools

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Chat. |
| `GET` | `/bookings` | List bookings. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /chat`

Chat.

### Request

```json
{
  "messages": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | `array` | no | Messages |

### Response `200`

```json
{"response": msg["content"], "bookings": "<string>"}
```

---

## `GET /bookings`

List all bookings.

### Response `200`

```json
{"bookings": null}
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

## Error Handling

All endpoints return JSON. On error:

```json
{
  "bookings": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
