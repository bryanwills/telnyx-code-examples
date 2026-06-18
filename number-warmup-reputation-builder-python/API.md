# API Reference — Number Warmup & Reputation Builder

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/warmup/start` | Start warmup. |
| `POST` | `/warmup/send` | Send warmup. |
| `GET` | `/warmup/status` | Warmup status. |
| `POST` | `/warmup/reset-daily` | Reset daily. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /warmup/start`

Start warmup.

### Request

```json
{
  "number": "number-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string` | **yes** | Number |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /warmup/send`

Send warmup.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from_number` | `string` | **yes** | From number |
| `to` | `string` | **yes** | Destination phone number (E.164) |
| `text` | `string` | no | Text content |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /warmup/status`

Warmup status.

### Response `200`

```json
{"numbers": null}
```

---

## `POST /warmup/reset-daily`

Reset daily.

### Response `200`

```json
{
  "status": "reset",
  "numbers": "<string>"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "numbers": [
    {
      "id": "abc-123",
      "status": "active"
    }
  ]
}
```

---

## Status Values

Records use these status values: `ok`, `reset`, `sent`, `started`, `warming`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "status": "reset",
  "numbers": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
