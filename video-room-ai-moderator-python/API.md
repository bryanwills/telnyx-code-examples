# API Reference — Video Room AI Moderator

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/rooms` | Create a new room. |
| `GET` | `/rooms` | List rooms. |
| `POST` | `/rooms/<room_id>/tokens` | Create a new token. |
| `POST` | `/moderate` | Moderate message. |
| `GET` | `/moderation-log` | Get log. |
| `DELETE` | `/rooms/<room_id>` | Delete room. |
| `GET` | `/health` | Health check and service status. |

---

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

---

## `GET /rooms`

List all rooms.

### Response `200`

```json
{
  "error": "Error description"
}
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

---

## `GET /moderation-log`

Get a specific log by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
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

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "log": "example-value"
}
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
