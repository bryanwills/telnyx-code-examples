## `GET /sim-cards`

List all sims.

### Response `200`

```json
{"data": null}
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
  "data": []
}
```

**Try it:**

```bash
curl http://localhost:5000/sim-cards/example-id
```

---

## `POST /sim-cards/<sim_card_id>/activate`

Activate sim.

### Response `200`

```json
{"message": "SIM card activated successfully", "data": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/sim-cards/example-id/activate \
  -H "Content-Type: application/json" \
  -d '{"message": "SIM card activated successfully", "data": null}'
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
