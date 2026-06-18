## `POST /rooms`

Create a new room.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agenda` | `array` | no | Agenda |
| `duration_minutes` | `string` | no | Duration minutes |
| `name` | `string` | no | Display name or label |
| `max_participants` | `string` | no | Max participants |
| `id` | `string` | **yes** | Id |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/rooms \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /rooms/<room_id>/start`

Start meeting.

### Response `200`

```json
{
  "error": "Room not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/rooms/example-id/start \
  -H "Content-Type: application/json" \
  -d '{"error": "Room not found"}'
```

---

## `GET /rooms/<room_id>/status`

Meeting status.

### Response `200`

```json
{
  "error": "Room not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/rooms/example-id/status
```

---

## `POST /rooms/<room_id>/next`

Next topic.

### Response `200`

```json
{
  "error": "Room not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/rooms/example-id/next \
  -H "Content-Type: application/json" \
  -d '{"error": "Room not found"}'
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "rooms": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `active`, `all_topics_completed`, `completed`, `no_active_topic`, `ok`, `pending`, `started`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "ok",
  "rooms": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
