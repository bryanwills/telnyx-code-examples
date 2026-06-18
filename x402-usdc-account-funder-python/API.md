# API Reference — x402 USDC Account Funder

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/quote` | Get quote. |
| `POST` | `/pay` | Submit payment. |
| `GET` | `/balance` | Get balance. |
| `GET` | `/info` | Payment info. |
| `GET` | `/quotes` | List quotes. |
| `GET` | `/payments` | List payments. |
| `GET` | `/health` | Health check and service status. |

---

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

---

## `GET /balance`

Get a specific balance by ID.

### Response `200`

```json
{
  "error": "Error description"
}
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

---

## `GET /quotes`

List all quotes.

### Response `200`

```json
{"quotes": quotes[-20:]}
```

---

## `GET /payments`

List all payments.

### Response `200`

```json
{"payments": payments[-20:]}
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
