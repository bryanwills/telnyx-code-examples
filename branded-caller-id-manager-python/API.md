## `POST /brands`

Create a new brand.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_type` | `string` | no | Entity type |
| `display_name` | `string` | **yes** | Display name |
| `company_name` | `string` | **yes** | Company name |
| `ein` | `string` | **yes** | Ein |
| `phone` | `string` | **yes** | Phone number in E.164 format (e.g., `+12125551234`) |
| `street` | `string` | **yes** | Street |
| `city` | `string` | **yes** | City |
| `state` | `string` | **yes** | State |
| `postal_code` | `string` | **yes** | Postal code |
| `country` | `string` | no | Country |
| `vertical` | `string` | no | Vertical |
| `website` | `string` | **yes** | Website |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/brands \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `GET /brands`

List all brands.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/brands
```

---

## `POST /campaigns`

Create a new campaign.

### Request

```json
{
  "error": "example-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `brand_id` | `string` | **yes** | Brand id |
| `usecase` | `string` | no | Usecase |
| `description` | `string` | **yes** | Description |
| `sample_message` | `string` | no | Sample message |
| `phone_numbers` | `array` | no | Phone numbers |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/campaigns \
  -H "Content-Type: application/json" \
  -d '{"error": "example-value"}'
```

---

## `PUT /numbers/<number>/caller-id`

Update caller id.

### Request

```json
{
  "campaigns": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `business_name` | `string` | no | Business name |

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X PUT http://localhost:5000/numbers/example-id/caller-id \
  -H "Content-Type: application/json" \
  -d '{"campaigns": []}'
```

---

## `GET /stir-shaken/status`

Stir shaken status.

### Response `200`

```json
{
  "number": "example-value",
  "cnam_enabled": "example-value",
  "caller_id_name": "example-value",
  "purchased_at": "2026-06-18T21:00:00Z"
}
```

**Try it:**

```bash
curl http://localhost:5000/stir-shaken/status
```

---

## `GET /campaigns`

List all campaigns.

### Response `200`

```json
{"campaigns": null}
```

**Try it:**

```bash
curl http://localhost:5000/campaigns
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "campaigns": "<string>"
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
  "status": "ok",
  "campaigns": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
