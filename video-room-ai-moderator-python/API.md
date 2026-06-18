## `POST /rooms`

Create a new room.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | no | Display name or label |
| `max_participants` | `string` | no | Max participants |
| `record` | `boolean` | no | Record |
| `name` | `string` | **yes** | Display name or label |
| `rules` | `string` | no | Rules |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/rooms \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `GET /rooms`

List all rooms.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/rooms
```

---

## `POST /rooms/<room_id>/tokens`

Create a new token.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/rooms/example-id/tokens \
  -H "Content-Type: application/json" \
  -d '{"error": "Error description"}'
```

---

## `POST /moderate`

Moderate message.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `room_id` | `string` | **yes** | Room id |
| `message` | `string` | no | Message content to send |
| `sender` | `string` | no | Sender |

### Response `200`

```json
{"moderation": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/moderate \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /moderation-log`

Get a specific log by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/moderation-log
```

---

## `DELETE /rooms/<room_id>`

Delete room.

### Response `200`

```json
{
  "status": "deleted"
}
```

**Try it:**

```bash
curl -X DELETE http://localhost:5000/rooms/example-id
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "log": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `deleted`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "deleted"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
