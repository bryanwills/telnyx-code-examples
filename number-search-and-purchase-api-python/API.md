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

**Try it:**

```bash
curl http://localhost:5000/numbers/search
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

**Try it:**

```bash
curl -X POST http://localhost:5000/numbers/purchase \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
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

**Try it:**

```bash
curl http://localhost:5000/numbers/inventory
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

**Try it:**

```bash
curl http://localhost:5000/health
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
