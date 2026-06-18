# API Reference — Production-ready Flask application for SIM card activation via Telnyx.

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sim-cards` | List sims. |
| `GET` | `/sim-cards/<sim_card_id>` | Get sim. |
| `POST` | `/sim-cards/<sim_card_id>/activate` | Activate sim. |

---

## `GET /sim-cards`

List all sims.

### Response `200`

```json
{"data": null}
```

---

## `GET /sim-cards/<sim_card_id>`

Get a specific sim by ID.

### Response `200`

```json
{
  "data": []
}
```

---

## `POST /sim-cards/<sim_card_id>/activate`

Activate sim.

### Response `200`

```json
{"message": "SIM card activated successfully", "data": null}
```

---

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
