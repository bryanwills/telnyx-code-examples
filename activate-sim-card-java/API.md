# API Reference

This example exposes one HTTP route. All requests and responses are JSON.

## `POST /sim/activate`

Activate (enable) a Telnyx IoT SIM card by its SIM card ID.

### Request

```json
{
  "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sim_card_id` | `string` | **yes** | Telnyx SIM card ID (UUID) to enable |

### Response `200`

```json
{
  "id": "8a4c1b9e-4f2a-4c3d-9e21-8b7c6d5e4f3a",
  "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158",
  "status": "in-progress",
  "message": "SIM card enable requested"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | SIM-card action ID returned by the enable operation (the action is asynchronous) |
| `sim_card_id` | `string` | The SIM card ID that was submitted for activation |
| `status` | `string` | Status of the enable action (e.g. `in-progress`) |
| `message` | `string` | Human-readable confirmation |

**Try it:**

```bash
curl -X POST http://localhost:8080/sim/activate \
  -H "Content-Type: application/json" \
  -d '{"sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"}'
```

---

## Telnyx API Endpoints Called

The application calls the Telnyx Java SDK method `client.simCards().actions().enable(simCardId)`, which maps to:

- **Enable (activate) SIM Card**: `POST /v2/sim_cards/{id}/actions/enable` — [API reference](https://developers.telnyx.com/api-reference/sim-cards/enable-sim-card)

The SDK returns an `ActionEnableResponse`; `response.data()` is an `Optional<SimCardAction>` whose `id()` and `status()` accessors return `Optional` values.

---

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success — SIM enable request accepted |
| `400` | Bad request — missing or empty `sim_card_id`, or invalid JSON |
| `401` | Invalid API key |
| `404` | SIM card not found |
| `405` | Method not allowed — use `POST` |
| `422` | SIM card cannot be activated from its current status |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |
| `502` | Upstream Telnyx API error (other non-mapped status) |

Upstream error details from the Telnyx API are logged server-side and are never included in the HTTP response body.
