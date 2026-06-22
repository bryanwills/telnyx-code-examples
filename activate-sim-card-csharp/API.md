# API Reference — Activate a SIM Card (C# / .NET)

This service exposes three routes. All responses are JSON.

Base URL (local default): `http://localhost:5000`

---

## `POST /sim-cards/{id}/enable`

Enable (activate) a SIM card. Internally calls `SimCardsService.EnableAsync(id)`, which
issues `POST /v2/sim_cards/{id}/actions/enable` (empty JSON body) to the Telnyx API and
parses the `data` token into a `SimCardRecord`.

### Path parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | `string` | yes | The Telnyx SIM card id (UUID). |

### Request body

None.

### Responses

| Status | Body | When |
|--------|------|------|
| `200 OK` | `{ "id": string, "status": string, "message": string }` | Enable request accepted by Telnyx |
| `400 Bad Request` | `{ "error": "SIM card id is required." }` | Empty/whitespace id |
| `502 Bad Gateway` | RFC 7807 problem (`title: "Failed to enable SIM card."`) | Telnyx returned an error (`TelnyxException`) |
| `500 Internal Server Error` | RFC 7807 problem (`title: "Internal server error."`) | Unexpected error |

### Example

```bash
curl -X POST http://localhost:5000/sim-cards/6b14e151-8493-4fa1-8664-1cc4e6d14158/enable
```

```json
{
  "id": "6b14e151-8493-4fa1-8664-1cc4e6d14158",
  "status": "enabling",
  "message": "SIM card enable requested."
}
```

> The `status` field reflects whatever the Telnyx API returns on the `SimCardRecord`
> (e.g. `enabling`, then `enabled` once provisioning completes). Errors never leak
> exception detail to the caller — details are logged server-side via `ILogger`.

---

## `POST /webhooks/sim`

Receive an inbound Telnyx webhook. The handler reads the **raw** request body (before any
JSON parsing), then verifies the signature with
`Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(rawBody, signature, timestamp, publicKey)`.

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `telnyx-signature-ed25519` | yes | Base64 Ed25519 signature of `"{timestamp}|{rawBody}"` |
| `telnyx-timestamp` | yes | Unix timestamp; must be within 300s tolerance |

### Request body

The raw Telnyx event JSON. After verification, event fields are read from `evt.Data`
(`EventType`, `Id`, `OccurredAt`, `RecordType`, `Payload`). The `data.payload` object
carries the SIM/event details.

### Responses

| Status | Body | When |
|--------|------|------|
| `200 OK` | `{ "received": true, "event_type": string }` | Signature valid; event accepted |
| `401 Unauthorized` | empty | Invalid signature or timestamp outside tolerance (`TelnyxException`) |
| `500 Internal Server Error` | RFC 7807 problem | `TELNYX_PUBLIC_KEY` not configured |

---

## `GET /health`

Liveness probe.

### Responses

| Status | Body |
|--------|------|
| `200 OK` | `{ "status": "ok" }` |

---

## SDK call mapping

| Route | SDK call | Telnyx endpoint |
|-------|----------|-----------------|
| `POST /sim-cards/{id}/enable` | `new SimCardsService().EnableAsync(id)` | `POST /v2/sim_cards/{id}/actions/enable` |
| `POST /webhooks/sim` | `Webhook.ConstructEvent(rawBody, sig, ts, pubKey)` | n/a (local verification) |

Configuration is global: `TelnyxConfiguration.SetApiKey(apiKey)`. All SDK failures throw a
single `Telnyx.TelnyxException`.
