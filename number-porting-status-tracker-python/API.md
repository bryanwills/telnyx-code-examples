## `GET /ports/list`

List all ports.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/ports/list
```

---

## `POST /ports/create`

Create a new port.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_numbers` | `array` | no | Phone numbers |

### Response `200`

```json
{"error": resp.text}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/ports/create \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `POST /webhooks/porting`

Receives Telnyx porting status webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/porting
```

## `GET /ports/<order_id>`

Get a specific port by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/ports/example-id
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

Records use these status values: `ok`, `submitted`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Not found"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
