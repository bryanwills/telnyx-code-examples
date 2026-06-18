# API Reference — Number Search and Purchase API

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/numbers/search` | Search numbers. |
| `POST` | `/numbers/purchase` | Purchase number. |
| `GET` | `/numbers/inventory` | List inventory. |
| `GET` | `/health` | Health check and service status. |

---

## `GET /numbers/search`

Search numbers.

### Response `200`

```json
{
  "numbers": "example-value",
  "features": "example-value",
  "cost": "example-value"
}
```

---

## `POST /numbers/purchase`

Purchase number.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_numbers` | `array` | no | Phone numbers |

### Response `200`

```json
{"results": null}
```

---

## `GET /numbers/inventory`

List all inventory.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "purchases": "<string>"
}
```

---

## Status Values

Records use these status values: `error`, `failed`, `ok`, `ordered`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Error description"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
