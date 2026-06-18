## `POST /esim/profiles`

Provision esim.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `device_name` | `string` | **yes** | Device name |
| `sim_card_group_id` | `string` | **yes** | Sim card group id |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/esim/profiles \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /esim/profiles/<sim_card_id>/activate`

Activate esim.

### Response `200`

```json
{
  "error": "sim_card_id is required"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/esim/profiles/example-id/activate \
  -H "Content-Type: application/json" \
  -d '{"error": "sim_card_id is required"}'
```

---

## `GET /esim/profiles/<sim_card_id>`

Get a specific esim by ID.

### Response `200`

```json
{
  "error": "sim_card_id is required"
}
```

**Try it:**

```bash
curl http://localhost:5000/esim/profiles/example-id
```

---

## `GET /esim/profiles`

List all esims.

### Response `200`

```json
{
  "error": "limit must be between 1 and 100"
}
```

**Try it:**

```bash
curl http://localhost:5000/esim/profiles
```

---

## `POST /esim/webhooks/sim-status`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/esim/webhooks/sim-status
```

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
