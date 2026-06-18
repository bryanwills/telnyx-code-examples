# API Reference — Number Lookup Fraud Screener

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/screen/<number>` | Screen number. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `POST` | `/blocklist` | Add to blocklist. |
| `GET` | `/blocklist` | List blocklist. |
| `GET` | `/screening-log` | Get log. |
| `GET` | `/health` | Health check and service status. |

---

## `GET /screen/<number>`

Screen number.

### Response `200`

```json
{"number": null, "action": "block", "reason": "blocklisted"}
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `POST /blocklist`

Add to blocklist.

### Request

```json
{
  "number": "number-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string` | **yes** | Number |

### Response `200`

```json
{"status": "blocked", "number": null}
```

---

## `GET /blocklist`

List all blocklist.

### Response `200`

```json
{
  "blocked": "<string>"
}
```

---

## `GET /screening-log`

Get a specific log by ID.

### Response `200`

```json
{"log": null}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "screened": "<string>",
  "blocked": "<string>"
}
```

---

## Status Values

Records use these status values: `blocked`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "number": "example-value",
  "action": "block",
  "reason": "blocklisted"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
