# API Reference — WhatsApp-SMS Bridge

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/bridge` | Create a new bridge. |
| `POST` | `/webhooks/messaging` | Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly. |
| `GET` | `/bridges` | List bridges. |
| `GET` | `/messages` | List messages. |
| `GET` | `/health` | Health check and service status. |

---

## `POST /bridge`

Create a new bridge.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sms_number` | `string` | **yes** | Sms number |
| `whatsapp_number` | `string` | **yes** | Whatsapp number |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

## `GET /bridges`

List all bridges.

### Response `200`

```json
{"bridges": null}
```

---

## `GET /messages`

List all messages.

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
{"status": "ok", "bridges": "<string>" // 2, "messages": "<string>"}
```

---

## Status Values

Records use these status values: `bridged`, `forwarded`, `ignored`, `no_bridge`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "bridges": []
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
