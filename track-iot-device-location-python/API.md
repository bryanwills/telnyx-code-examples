## `GET /devices`

List all devices.

### Response `200`

```json
{"devices": null}
```

**Try it:**

```bash
curl http://localhost:5000/devices
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

**Try it:**

```bash
curl http://localhost:5000/devices/example-id
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

**Try it:**

```bash
curl http://localhost:5000/devices/example-id/location
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

**Try it:**

```bash
curl http://localhost:5000/health
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
