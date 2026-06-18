# API Reference — Send MMS Picture Message

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/mms/send` | Send mms endpoint. |

---

## `POST /mms/send`

Send mms.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number (E.164) |
| `message` | `string` | **yes** | Message content to send |
| `media_urls` | `array` | no | Media urls |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

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
