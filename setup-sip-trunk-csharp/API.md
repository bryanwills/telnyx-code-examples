# API Reference — setup-sip-trunk-csharp

Typed endpoint reference for the minimal ASP.NET app. All endpoints return JSON.

---

## `POST /sip/connections`

Create a credential-authenticated SIP connection.

### Request

```json
{
  "name": "office-pbx",
  "username": "myuser12345",
  "password": "mySecret1234567",
  "active": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Human-readable connection name (sent to the SDK as `ConnectionName`) |
| `username` | `string` | **yes** | SIP credential username (sent as `UserName`) |
| `password` | `string` | **yes** | SIP credential password (sent as `Password`; never returned) |
| `active` | `bool` | no | Whether the connection is active. Defaults to `true` |

### Response `201`

```json
{
  "id": "1293384261075731499",
  "connection_name": "office-pbx",
  "username": "myuser12345",
  "active": true,
  "sip_uri_calling_preference": "disabled"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Telnyx credential connection ID |
| `connection_name` | `string` | Connection name |
| `username` | `string` | SIP credential username |
| `active` | `bool` | Whether the connection is active |
| `sip_uri_calling_preference` | `string` | SIP URI calling preference (e.g. `disabled`) |

**Try it:**

```bash
curl -X POST http://localhost:5000/sip/connections \
  -H "Content-Type: application/json" \
  -d '{"name":"office-pbx","username":"myuser12345","password":"mySecret1234567","active":true}'
```

---

## `GET /sip/connections`

List credential connections on the account.

### Request

| Param | Type | In | Required | Description |
|-------|------|----|----------|-------------|
| `page` | `int` | query | no | Page number (maps to `page[number]`). Defaults to `1` |
| `pageSize` | `int` | query | no | Page size (maps to `page[size]`). Defaults to `20` |

### Response `200`

```json
{
  "data": [
    {
      "id": "1293384261075731499",
      "connection_name": "office-pbx",
      "username": "myuser12345",
      "active": true,
      "sip_uri_calling_preference": "disabled"
    }
  ]
}
```

Returns an object with a `data` array; each element has the same fields as the create response.

**Try it:**

```bash
curl "http://localhost:5000/sip/connections?page=1&pageSize=20"
```

---

## `GET /sip/connections/{id}`

Retrieve a single credential connection by ID.

### Request

| Param | Type | In | Required | Description |
|-------|------|----|----------|-------------|
| `id` | `string` | path | **yes** | Telnyx credential connection ID |

### Response `200`

```json
{
  "id": "1293384261075731499",
  "connection_name": "office-pbx",
  "username": "myuser12345",
  "active": true,
  "sip_uri_calling_preference": "disabled"
}
```

**Try it:**

```bash
curl http://localhost:5000/sip/connections/1293384261075731499
```

---

## `POST /webhooks/telnyx`

Receive an inbound Telnyx webhook. The raw body is read before any parsing and verified with the Telnyx Ed25519 signature via `Webhook.ConstructEvent`. Event fields are read from `data` and `data.payload`.

### Request headers

| Header | Required | Description |
|--------|----------|-------------|
| `telnyx-signature-ed25519` | **yes** | Base64 Ed25519 signature over `"{timestamp}|{raw body}"` |
| `telnyx-timestamp` | **yes** | Unix timestamp; must be within 300s tolerance |

### Responses

| Status | Meaning |
|--------|---------|
| `200` | Signature verified; event accepted |
| `401` | Bad signature or stale timestamp |
| `500` | `TELNYX_PUBLIC_KEY` not configured |

---

## Telnyx SDK Calls

The app wraps these Telnyx SIP Trunking endpoints via the `Telnyx.net` SDK's `CredentialConnectionService`:

| SDK call | Telnyx endpoint | Used by |
|----------|-----------------|---------|
| `svc.CreateCredentialConnectionAsync(UpsertCredentialConnectionOptions)` | `POST /v2/credential_connections` | `POST /sip/connections` |
| `svc.ListCredentialConnectionAsync(ConnectionListOptions)` | `GET /v2/credential_connections` | `GET /sip/connections` |
| `svc.RetrieveCredentialConnectionAsync(id)` | `GET /v2/credential_connections/{id}` | `GET /sip/connections/{id}` |
| `Telnyx.net.Infrastructure.Public.Webhook.ConstructEvent(...)` | n/a (signature verification) | `POST /webhooks/telnyx` |

## Error Handling

Every SDK call throws a single `Telnyx.TelnyxException`. The detail is logged server-side and never leaked in the HTTP response.

| Status | Meaning |
|--------|---------|
| `200` | Success (list / retrieve) |
| `201` | Created (new credential connection) |
| `400` | Bad request — missing required fields |
| `401` | Webhook signature invalid |
| `500` | Server misconfiguration (e.g. missing public key) |
| `502` | Upstream Telnyx API error |
