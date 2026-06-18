# API Reference — Commercial Voice-Over Generator

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/commercials/generate` | Generate commercial. |
| `GET` | `/commercials/<campaign_id>` | Get campaign. |
| `GET` | `/commercials` | List campaigns. |
| `GET` | `/options` | List options. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /commercials/generate`

Generate commercial.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product` | `string` | no | Product |
| `audience` | `string` | no | Audience |
| `tone` | `string` | no | Tone |
| `length` | `string` | no | Length |
| `cta` | `string` | no | Cta |
| `client_phone` | `string` | no | Client phone |

### Response `200`

```json
{"error": "Provide "product" name/description"}
```

---

## `GET /commercials/<campaign_id>`

Get a specific campaign by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /commercials`

List all campaigns.

### Response `200`

```json
{
  "error": "Campaign not found"
}
```

---

## `GET /options`

List all options.

### Response `200`

```json
{
  "spot_lengths": "example-value",
  "tones": "example-value"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_campaigns": "example-value",
  "version": "1.0.0"
}
```

---

## Status Values

Records use these status values: `complete`, `failed`, `ok`, `rendering`, `writing`

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
