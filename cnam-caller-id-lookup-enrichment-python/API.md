# API Reference — CNAM Caller ID Lookup Enrichment

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/lookup/<number>` | Lookup number. |
| `POST` | `/lookup/batch` | Batch lookup. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/enrichments` | List enrichments. |
| `GET` | `/health` | Health check and service status. |

---

## `GET /lookup/<number>`

Lookup number.

### Response `200`

```json
{
  "result": "example-value",
  "source": "cache"
}
```

---

## `POST /lookup/batch`

Batch lookup.

### Request

```json
{
  "numbers": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numbers` | `array` | no | List of phone numbers |

### Response `200`

```json
{"results": null, "total": "<string>"}
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /enrichments`

List all enrichments.

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
  "cached": "<string>",
  "enrichments": "<string>"
}
```

---

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
