# API Reference — Set Up a SIP Trunk (PHP)

The vanilla PHP front controller (`index.php`) exposes five HTTP routes. All responses are JSON.

## `POST /connections`

Create a credential (SIP) connection.

### Request

Body: `application/json`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connectionName` | `string` | **yes** | Human-readable name for the SIP connection |
| `userName` | `string` | **yes** | SIP auth username, 4–32 alphanumeric characters |
| `password` | `string` | **yes** | SIP auth password, 8–128 characters. Never returned in the response |

### Response `201`

```json
{
  "id": "1234567890",
  "connectionName": "My SIP Trunk",
  "userName": "myuser1234",
  "active": true,
  "createdAt": "2026-06-19T12:00:00.000Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string \| null` | Credential connection ID |
| `connectionName` | `string \| null` | The connection name |
| `userName` | `string \| null` | The SIP auth username |
| `active` | `bool \| null` | Whether the connection is active |
| `createdAt` | `string \| null` | ISO 8601 creation timestamp |

---

## `GET /connections`

List credential (SIP) connections.

### Request

No path params, body, or query params (the example calls `list()` with defaults).

### Response `200`

```json
{
  "data": [
    {
      "id": "1234567890",
      "connectionName": "My SIP Trunk",
      "userName": "myuser1234",
      "active": true,
      "createdAt": "2026-06-19T12:00:00.000Z"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data` | `array` | Array of connection objects (same shape as `POST /connections`) |

---

## `GET /connections/{id}`

Retrieve a single credential (SIP) connection by ID.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` (path) | `string` | **yes** | Telnyx credential connection ID |

No request body.

### Response `200`

```json
{
  "id": "1234567890",
  "connectionName": "My SIP Trunk",
  "userName": "myuser1234",
  "active": true,
  "createdAt": "2026-06-19T12:00:00.000Z"
}
```

Same field shape as the `POST /connections` response.

---

## `POST /webhooks/telnyx`

Receive Telnyx webhooks. The handler reads the raw body via `file_get_contents('php://input')` and the headers via `getallheaders()`, then calls `$client->webhooks->unwrap($body, $headers)`, which verifies the `Telnyx-Signature-Ed25519` header (with a 300s timestamp tolerance) before the event is parsed. Fields are read from `data.payload` per the Telnyx v2 webhook shape.

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

The code calls the Telnyx Credential Connections API through the PHP SDK:

| SDK call | Telnyx endpoint | Used by route |
|----------|-----------------|---------------|
| `$client->credentialConnections->create(connectionName:, userName:, password:)` | `POST /v2/credential_connections` | `POST /connections` |
| `$client->credentialConnections->list()` | `GET /v2/credential_connections` | `GET /connections` |
| `$client->credentialConnections->retrieve($id)` | `GET /v2/credential_connections/{id}` | `GET /connections/{id}` |
| `$client->webhooks->unwrap($body, $headers)` | (signature verification) | `POST /webhooks/telnyx` |

`create()` returns a `CredentialConnectionNewResponse`; read fields from `->data` (`id`, `connectionName`, `userName`, `active`, `createdAt`). `list()` returns a `DefaultFlatPagination<CredentialConnection>`; iterate with `$page->getItems()`. `retrieve()` returns a `CredentialConnectionGetResponse`; read fields from `->data`. All properties are camelCase typed properties.

## Error Handling

Telnyx SDK exceptions (from `Telnyx\Core\Exceptions\`) are mapped to HTTP status codes. Exception details are logged via `error_log()`; clients only receive generic messages.

| Status | Meaning | Body |
|--------|---------|------|
| `201` | Connection created | `{"id": "...", "connectionName": "...", ...}` |
| `400` | Missing required fields, or bad request to Telnyx (`BadRequestException`) | `{"error": "..."}` |
| `401` | Authentication failed (`AuthenticationException`) | `{"error": "Invalid API key"}` |
| `404` | Connection not found (`NotFoundException`) | `{"error": "Credential connection not found"}` |
| `429` | Rate limited (`RateLimitException`) | `{"error": "Rate limit exceeded. Please slow down."}` |
| `503` | Network error (`APIConnectionException`) | `{"error": "Network error connecting to Telnyx"}` |
| `500` | Unexpected server error | `{"error": "Internal server error"}` |

Other `APIException` subclasses surface the upstream status (via the public `$e->status` property) with a generic `{"error": "Telnyx API error"}` body.
