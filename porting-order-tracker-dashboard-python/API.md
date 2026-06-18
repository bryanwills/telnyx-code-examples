## `POST /porting/orders`

Submit order.

### Request

```json
{
  "order": "example-value",
  "api": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_numbers` | `array` | no | Phone numbers |
| `authorized_person` | `string` | **yes** | Authorized person |
| `current_provider` | `string` | **yes** | Current provider |
| `billing_phone_number` | `string` | **yes** | Billing phone number |
| `reference` | `string` | no | Reference |
| `phone_numbers` | `string` | **yes** | Phone numbers |
| `phone_numbers` | `array` | no | Phone numbers |
| `current_provider` | `string` | **yes** | Current provider |

### Response `200`

```json
{"order": null, "api": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/porting/orders \
  -H "Content-Type: application/json" \
  -d '{"order": "example-value", "api": "example-value"}'
```

---

## `POST /porting/bulk`

Bulk submit.

### Request

```json
{
  "batches": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `batches` | `array` | no | Batches |

### Response `200`

```json
{"submitted": "<string>", "results": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/porting/bulk \
  -H "Content-Type: application/json" \
  -d '{"batches": []}'
```

---

## `GET /porting/orders`

List all orders.

### Response `200`

```json
{
  "order": "example-value",
  "api": {
    "key": "value"
  }
}
```

**Try it:**

```bash
curl http://localhost:5000/porting/orders
```

---

## `POST /webhooks/porting`

Receives Telnyx porting status webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/porting
```

## `GET /porting/sla-check`

Sla check.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/porting/sla-check
```

---

## `GET /porting/dashboard`

Dashboard.

### Response `200`

```json
{
  "error": "Error description",
  "local": []
}
```

**Try it:**

```bash
curl http://localhost:5000/porting/dashboard
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "orders": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `error`, `ok`, `received`, `submitted`

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
