# API Reference — Production-ready Flask application for device location

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/devices` | List devices. |
| `GET` | `/devices/<sim_card_id>` | Get device location. |
| `GET` | `/devices/<sim_card_id>/location` | Get location only. |
| `GET` | `/health` | Health check and service status. |

---

## `GET /devices`

List all devices.

### Response `200`

```json
{"devices": null}
```

---

## `GET /devices/<sim_card_id>`

Get device location.

### Response `200`

```json
{
  "devices": []
}
```

---

## `GET /devices/<sim_card_id>/location`

Get location only.

### Response `200`

```json
{
  "error": "Invalid SIM card ID format"
}
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "healthy"
}
```

---

## Status Values

Records use these status values: `healthy`, `unhealthy`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Invalid SIM card ID format"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
