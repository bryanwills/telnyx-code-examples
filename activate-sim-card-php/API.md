# API Reference — Activate SIM Card (PHP)

The vanilla PHP front controller (`index.php`) exposes four HTTP routes. All responses are JSON.

## `GET /sim/{id}`

Retrieve the current state of a single SIM card.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` (path) | `string` | **yes** | Telnyx SIM card ID (UUID) |

No request body.

### Response `200`

```json
{
  "id": "6b14e151-8493-4fa1-8664-1cc4e6d14158",
  "iccid": "89310410106543789301",
  "status": "disabled",
  "simCardGroupId": "47a9c0fa-1d3b-4f2a-9e22-2c4e9a1b7d10"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | SIM card ID |
| `iccid` | `string \| null` | Integrated Circuit Card Identifier |
| `status` | `string \| null` | Current SIM status (e.g. `disabled`, `enabled`) |
| `simCardGroupId` | `string \| null` | ID of the SIM card group |

---

## `POST /sim/{id}/activate`

Enable (activate) a SIM card by ID. The SIM must already belong to a SIM card group. Activation is **asynchronous**, so the route returns `202 Accepted` with the started action.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` (path) | `string` | **yes** | Telnyx SIM card ID to enable |

No request body.

### Response `202`

```json
{
  "message": "SIM card activation requested",
  "action": {
    "actionId": "a1b2c3d4-0000-1111-2222-333344445555",
    "simCardId": "6b14e151-8493-4fa1-8664-1cc4e6d14158",
    "actionType": "enable",
    "status": "in-progress"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | `string` | Human-readable acknowledgement |
| `action.actionId` | `string \| null` | ID of the async SIM card action — poll it to follow status |
| `action.simCardId` | `string` | SIM card ID being enabled |
| `action.actionType` | `string` | Always `enable` for this route |
| `action.status` | `string \| null` | Action status (e.g. `in-progress`) |

---

## `POST /webhooks/telnyx`

Receive Telnyx SIM card webhooks. The handler reads the raw body via `file_get_contents('php://input')` and the headers via `getallheaders()`, then calls `$client->webhooks->unwrap($body, $headers)`, which verifies the `Telnyx-Signature-Ed25519` header (with a 300s timestamp tolerance) before the event is parsed. Fields are read from `data.payload` per the Telnyx v2 webhook shape.

### Response

| Status | Meaning | Body |
|--------|---------|------|
| `200` | Signature valid, event acknowledged | `{"received": true}` |
| `401` | Missing/invalid signature | `{"error": "Invalid webhook signature"}` |
| `400` | Malformed webhook request | `{"error": "Bad webhook request"}` |

---

## `GET /health`

Liveness probe.

### Response `200`

```json
{ "status": "ok" }
```

---

## Telnyx API endpoints called

The code calls the Telnyx IoT SIM API through the PHP SDK:

| SDK call | Telnyx endpoint | Used by route |
|----------|-----------------|---------------|
| `$client->simCards->retrieve($id)` | `GET /v2/sim_cards/{id}` | `GET /sim/{id}` |
| `$client->simCards->actions->enable(id: $id)` | `POST /v2/sim_cards/{id}/actions/enable` | `POST /sim/{id}/activate` |
| `$client->webhooks->unwrap($body, $headers)` | (signature verification) | `POST /webhooks/telnyx` |

## Error Handling

Telnyx SDK exceptions (from `Telnyx\Core\Exceptions\`) are mapped to HTTP status codes. Exception details are logged via `error_log()`; clients only receive generic messages.

| Status | Meaning | Body |
|--------|---------|------|
| `202` | Activation accepted | `{"message": "SIM card activation requested", "action": {...}}` |
| `400` | Invalid SIM card ID | `{"error": "SIM card ID must be a non-empty string"}` |
| `401` | Authentication failed (`AuthenticationException`) | `{"error": "Invalid API key"}` |
| `404` | SIM not found (`NotFoundException`) | `{"error": "SIM card not found"}` |
| `429` | Rate limited (`RateLimitException`) | `{"error": "Rate limit exceeded. Please slow down."}` |
| `503` | Network error (`APIConnectionException`) | `{"error": "Network error connecting to Telnyx"}` |
| `500` | Unexpected server error | `{"error": "Internal server error"}` |

Other `APIException` subclasses surface the upstream status (via the public `$e->status` property) with a generic `{"error": "Telnyx API error"}` body.
