## `POST /sim/activate`

Activate a Telnyx IoT SIM card by its SIM card ID.

### Request

```json
{
  "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sim_card_id` | `string` | **yes** | Telnyx SIM card ID (UUID) to activate |

### Response `200`

```json
{
  "id": "6b14e151-8493-4fa1-8664-1cc4e6d14158",
  "iccid": "89310410106543789301",
  "status": "enabling",
  "sim_card_group_id": "47a1c2c4-3f5d-4e0e-9b3b-1f1b2c3d4e5f"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | SIM card ID |
| `iccid` | `string` | Integrated Circuit Card Identifier of the SIM |
| `status` | `string` | Current SIM status (e.g. `enabling`) |
| `sim_card_group_id` | `string` | ID of the SIM card group the SIM belongs to |

**Try it:**

```bash
curl -X POST http://localhost:8080/sim/activate \
  -H "Content-Type: application/json" \
  -d '{"sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"}'
```

---

## Telnyx API Endpoints Called

The application calls the Telnyx Go SDK method `client.SimCards.Activate(simCardID, nil)`, which maps to:

- **Activate SIM Card**: `POST /v2/sim_cards/{id}/actions/enable` -- [API reference](https://developers.telnyx.com/api-reference/sim-cards/enable-sim-card)

---

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success — SIM activation accepted |
| `400` | Bad request — missing `sim_card_id` or other validation error |
| `401` | Invalid API key |
| `429` | Rate limit exceeded |
| `503` | Network error connecting to Telnyx |

For `APIStatusError` responses, the body also includes a `status_code` field echoing the upstream HTTP status returned by the Telnyx API.
</content>
