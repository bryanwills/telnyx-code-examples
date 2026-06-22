# API Reference — Set Up a SIP Trunk (Java)

This service exposes a small REST API over the JDK's built-in HTTP server. It
proxies three Telnyx Credential Connections operations through the Telnyx Java
SDK. The SIP `password` is accepted on create but is never returned in any
response.

Base URL (local): `http://localhost:8080`

---

## `POST /sip-connections`

Create a credential (SIP) connection.

**Request headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

**Request body** (flat JSON object)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `connection_name` | `string` | yes | Human-readable connection name |
| `user_name` | `string` | yes | SIP username (must meet the Telnyx minimum length) |
| `password` | `string` | yes | SIP password; write-only, never returned |

**Maps to**

```
client.credentialConnections().create(
    CredentialConnectionCreateParams.builder()
        .connectionName(connection_name)
        .userName(user_name)
        .password(password)
        .build())
```

Telnyx endpoint: `POST /v2/credential_connections`

**Responses**

| Status | Body | When |
|--------|------|------|
| `201` | `Connection` object (see schema) | Connection created |
| `400` | `{ "error": string }` | Missing field or malformed JSON body |
| `405` | `{ "error": "Method not allowed" }` | Wrong HTTP method on the route |
| `502` | `{ "error": "Upstream Telnyx API error" }` | Telnyx API rejected the request (detail logged server-side) |
| `500` | `{ "error": "Internal server error" }` | Unexpected server error |

---

## `GET /sip-connections`

List credential connections. The SDK's auto-pager iterates across all result
pages.

**Maps to**

```
client.credentialConnections().list()   // CredentialConnectionListPage
// iterated via page.autoPager()
```

Telnyx endpoint: `GET /v2/credential_connections`

**Responses**

| Status | Body | When |
|--------|------|------|
| `200` | `{ "data": Connection[] }` | Success (possibly empty array) |
| `502` | `{ "error": "Upstream Telnyx API error" }` | Telnyx API error |
| `500` | `{ "error": "Internal server error" }` | Unexpected server error |

---

## `GET /sip-connections/{id}`

Retrieve a single credential connection by ID.

**Path parameters**

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `string` | yes | Credential connection ID |

**Maps to**

```
client.credentialConnections().retrieve(id)   // CredentialConnectionRetrieveResponse
```

Telnyx endpoint: `GET /v2/credential_connections/{id}`

**Responses**

| Status | Body | When |
|--------|------|------|
| `200` | `Connection` object | Found |
| `400` | `{ "error": "Connection id is required" }` | Empty ID |
| `502` | `{ "error": "Upstream Telnyx API error" }` | Telnyx API error (includes 404 from upstream) |
| `500` | `{ "error": "Internal server error" }` | Unexpected server error |

---

## `GET /health`

Liveness probe.

**Responses**

| Status | Body |
|--------|------|
| `200` | `{ "status": "ok" }` |

---

## Schemas

### `Connection` (response)

Derived from the SDK's `CredentialConnection` model. All SDK accessors return
`Optional`; a field is omitted from the JSON if the SDK does not populate it.

| Field | Type | Source accessor |
|-------|------|-----------------|
| `id` | `string` | `CredentialConnection.id()` |
| `connection_name` | `string` | `CredentialConnection.connectionName()` |
| `user_name` | `string` | `CredentialConnection.userName()` |

### Error

| Field | Type | Notes |
|-------|------|-------|
| `error` | `string` | Human-readable message. Upstream Telnyx error detail is logged via `java.util.logging`, never returned to the client. |

---

## SDK types

| Type | Package |
|------|---------|
| `TelnyxClient` | `com.telnyx.sdk.client` |
| `TelnyxOkHttpClient` | `com.telnyx.sdk.client.okhttp` |
| `CredentialConnectionCreateParams` | `com.telnyx.sdk.models.credentialconnections` |
| `CredentialConnectionCreateResponse` | `com.telnyx.sdk.models.credentialconnections` |
| `CredentialConnectionRetrieveResponse` | `com.telnyx.sdk.models.credentialconnections` |
| `CredentialConnectionListPage` | `com.telnyx.sdk.models.credentialconnections` |
| `CredentialConnection` | `com.telnyx.sdk.models.credentialconnections` |
| `TelnyxException` | `com.telnyx.sdk.errors` |
