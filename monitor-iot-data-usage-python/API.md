## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "service": "data-usage-monitor"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## `GET /sim-cards`

List all sims.

### Response `200`

```json
{"data": null, "count": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/sim-cards
```

---

## `GET /sim-cards/<sim_card_id>`

Get a specific sim by ID.

### Response `200`

```json
{
  "status": "ok",
  "service": "data-usage-monitor"
}
```

**Try it:**

```bash
curl http://localhost:5000/sim-cards/example-id
```

---

## `GET /sim-cards/<sim_card_id>/usage`

Get a specific usage by ID.

### Response `200`

```json
{
  "data": [],
  "count": 3
}
```

**Try it:**

```bash
curl http://localhost:5000/sim-cards/example-id/usage
```

---

## `GET /sim-cards/<sim_card_id>/health`

Health check and service status.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl http://localhost:5000/sim-cards/example-id/health
```

---

## `POST /sim-cards/<sim_card_id>/activate`

Activate sim.

### Response `200`

```json
{
            "id": response.data.id,
            "status": response.data.status,
            "message": "SIM card activated successfully",
        }
```

**Try it:**

```bash
curl -X POST http://localhost:5000/sim-cards/example-id/activate \
  -H "Content-Type: application/json" \
  -d '{
            "id": response.data.id,
            "status": response.data.status,
            "message": "SIM card activated successfully",
        }'
```

---

## `POST /webhooks/sim-events`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/sim-events
```

## Status Values

Records use these status values: `ok`, `received`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Invalid API key"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
