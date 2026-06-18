## `POST /quote`

Get a specific quote by ID.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount_usd` | `string` | no | Amount usd |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/quote \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /pay`

Submit payment.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quote_id` | `string` | **yes** | Quote id |
| `payment_signature` | `string` | **yes** | Payment signature |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/pay \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /balance`

Get a specific balance by ID.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/balance
```

---

## `GET /info`

Payment info.

### Response `200`

```json
{
  "chain": "Base",
  "chain_id": "example-value",
  "usdc_contract": "example-value",
  "min_amount": "$5.00",
  "max_amount": "$10",
  "quote_expiry": "5 minutes",
  "steps": "example-value"
}
```

**Try it:**

```bash
curl http://localhost:5000/info
```

---

## `GET /quotes`

List all quotes.

### Response `200`

```json
{"quotes": quotes[-20:]}
```

**Try it:**

```bash
curl http://localhost:5000/quotes
```

---

## `GET /payments`

List all payments.

### Response `200`

```json
{"payments": payments[-20:]}
```

**Try it:**

```bash
curl http://localhost:5000/payments
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "quotes": "<string>",
  "payments": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{
  "quotes": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
