# API Reference

This service exposes three HTTP routes. All responses are JSON.

---

## `POST /calls/dial`

Place an outbound Call Control call. Maps to `client.calls().dial(...)` → Telnyx `POST /v2/calls`.

### Request

```json
{
  "to": "+12125551234"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | `string` | **yes** | Destination phone number in E.164 format (must start with `+`). |

The caller ID (`from`) and `connection_id` are read from the environment (`TELNYX_PHONE_NUMBER`, `TELNYX_CONNECTION_ID`), not the request body.

### Response `200`

```json
{
  "call_control_id": "v3:uMi2qMWHT-mLFGkEm4t9tA",
  "from": "+15551234567",
  "to": "+12125551234"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `call_control_id` | `string` | Identifier for the call leg; use it for subsequent Call Control actions. |
| `from` | `string` | Caller ID used. |
| `to` | `string` | Destination number. |

### Errors

| Status | Body | Cause |
|--------|------|-------|
| `400` | `{"error":"Invalid JSON request body"}` | Body was not valid JSON. |
| `400` | `{"error":"Field 'to' is required and must be E.164 (e.g. +12125551234)"}` | Missing or non-E.164 `to`. |
| `405` | `{"error":"Method not allowed"}` | Method other than `POST`. |
| `502` | `{"error":"Failed to place call"}` | Upstream Telnyx call failed (detail is logged server-side, never returned). |

### Try it

```bash
curl -X POST http://localhost:8080/calls/dial \
  -H "Content-Type: application/json" \
  -d '{"to": "+12125551234"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control events (e.g. `call.answered`, `call.hangup`). The raw request body is read before parsing and verified with the Ed25519 signature via `client.webhooks().unwrap(...)`. Event fields are read from `data.payload`.

### Request headers

| Header | Required | Description |
|--------|----------|-------------|
| `telnyx-signature-ed25519` | **yes** | Base64 Ed25519 signature over `"{timestamp}|{body}"`. |
| `telnyx-timestamp` | **yes** | Unix seconds; enforced against a 300s replay window. |

The request body is the raw Telnyx event JSON (`{"data": {"event_type": ..., "payload": {...}}}`).

### Response `200`

```json
{
  "status": "received"
}
```

### Errors

| Status | Body | Cause |
|--------|------|-------|
| `400` | `{"error":"Missing Telnyx signature headers"}` | Signature/timestamp header absent. |
| `401` | `{"error":"Invalid webhook signature"}` | Signature/timestamp invalid, stale, or `TELNYX_PUBLIC_KEY` not configured. |
| `405` | `{"error":"Method not allowed"}` | Method other than `POST`. |

---

## `GET /health`

Liveness probe.

### Response `200`

```json
{
  "status": "ok"
}
```
