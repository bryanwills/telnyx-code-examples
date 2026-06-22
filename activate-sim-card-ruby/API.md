# API Reference

Typed reference for the endpoints exposed by this example.

---

## `POST /sim/activate`

Activate (enable) a Telnyx IoT SIM card by its SIM card ID.

### Request

`Content-Type: application/json`

```json
{
  "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sim_card_id` | `string` | **yes** | Telnyx SIM card ID (UUID) to enable. The SIM must already belong to a SIM card group. |

### Response `200`

```json
{
  "id": "f1f7e3a0-1c2b-4d3e-9a8b-0c1d2e3f4a5b",
  "status": "in-progress",
  "action_type": "enable",
  "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | SIM card action ID (the enable action, not the SIM card itself) |
| `status` | `string` | Status of the enable action (e.g. `in-progress`) |
| `action_type` | `string` | Action type, `enable` |
| `sim_card_id` | `string` | ID of the SIM card the action applies to |

> Enabling is **asynchronous**. A `200` means the request was accepted; the SIM transitions toward `enabled` afterward. Confirm via SIM status polling or the `sim_card.status_changed` webhook.

**Try it:**

```bash
curl -X POST http://localhost:4567/sim/activate \
  -H "Content-Type: application/json" \
  -d '{"sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158"}'
```

---

## `POST /webhooks/sim`

Receive SIM status-change webhooks from Telnyx. The signature is verified before the body is parsed.

### Request headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Telnyx-Signature-Ed25519` | `string` | **yes** | Base64 Ed25519 signature over `"<timestamp>\|<raw-body>"` |
| `Telnyx-Timestamp` | `string` | **yes** | Unix seconds; requests older than 300s are rejected (replay protection) |

### Request body (example)

```json
{
  "data": {
    "event_type": "sim_card.status_changed",
    "payload": {
      "id": "f1f7e3a0-1c2b-4d3e-9a8b-0c1d2e3f4a5b",
      "sim_card_id": "6b14e151-8493-4fa1-8664-1cc4e6d14158",
      "status": "enabled"
    }
  }
}
```

Event fields are read from `data.payload`.

### Response `200`

```json
{ "received": true }
```

---

## Telnyx API Endpoints Called

The application calls the Telnyx Ruby SDK method `client.sim_cards.actions.enable(sim_card_id)`, which maps to:

- **Enable SIM Card**: `POST /v2/sim_cards/{id}/actions/enable` — [API reference](https://developers.telnyx.com/api-reference/sim-cards/enable-sim-card)

---

## Error Handling

All endpoints return JSON. On error:

```json
{ "error": "Description of what went wrong" }
```

| Status | Meaning |
|--------|---------|
| `200` | Success — SIM enable accepted, or webhook received |
| `400` | Bad request — missing `sim_card_id` or invalid JSON |
| `401` | Invalid API key, or invalid/stale webhook signature |
| `429` | Rate limit exceeded |
| `500` | Unexpected internal error (details are logged, never returned) |
| `503` | Network error connecting to Telnyx |

For `Telnyx::Errors::APIStatusError` responses, the body also includes a `status_code` field echoing the upstream HTTP status returned by the Telnyx API.
