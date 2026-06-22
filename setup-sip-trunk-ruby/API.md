# API Reference

All endpoints accept and return JSON. Errors return `{"error": "..."}` with a
generic message (no internal/exception detail is leaked).

## `POST /sip/connections`

Create a new credential-authenticated SIP connection.

### Request

```json
{
  "name": "office-pbx",
  "username": "pbxuser01",
  "password": "s3cretp4ssw0rd"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Human-readable connection name (sent to Telnyx as `connection_name`) |
| `username` | `string` | **yes** | SIP credential username (sent as `user_name`, 4–32 chars) |
| `password` | `string` | **yes** | SIP credential password (≥ 8 chars) |

### Response `201`

```json
{
  "id": "1234567890",
  "connection_name": "office-pbx",
  "user_name": "pbxuser01",
  "status": "active",
  "created_at": "2026-06-18T12:00:00.000Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Telnyx credential connection ID |
| `connection_name` | `string` | Connection name |
| `user_name` | `string` | SIP credential username |
| `status` | `string` | `active` or `inactive` |
| `created_at` | `string` | ISO 8601 creation timestamp |

**Try it:**

```bash
curl -X POST http://localhost:4567/sip/connections \
  -H "Content-Type: application/json" \
  -d '{"name": "office-pbx", "username": "pbxuser01", "password": "s3cretp4ssw0rd"}'
```

---

## `GET /sip/connections/:id`

Retrieve a single SIP connection by ID.

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` (path) | **yes** | Telnyx credential connection ID |

### Response `200`

```json
{
  "id": "1234567890",
  "connection_name": "office-pbx",
  "user_name": "pbxuser01",
  "status": "active",
  "created_at": "2026-06-18T12:00:00.000Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Telnyx credential connection ID |
| `connection_name` | `string` | Connection name |
| `user_name` | `string` | SIP credential username |
| `status` | `string` | `active` or `inactive` |
| `created_at` | `string` | ISO 8601 creation timestamp |

**Try it:**

```bash
curl http://localhost:4567/sip/connections/1234567890
```

---

## `GET /sip/connections`

List SIP connections on the account (paginated).

### Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_number` | `number` (query) | no | Page number (default `1`) |
| `page_size` | `number` (query) | no | Items per page (default `20`) |

### Response `200`

```json
[
  {
    "id": "1234567890",
    "connection_name": "office-pbx",
    "user_name": "pbxuser01",
    "status": "active",
    "created_at": "2026-06-18T12:00:00.000Z"
  }
]
```

Returns an array of objects, each with `id`, `connection_name`, `user_name`,
`status`, and `created_at` as described above.

**Try it:**

```bash
curl "http://localhost:4567/sip/connections?page_number=1&page_size=20"
```

---

## `POST /webhooks/sip`

Receives inbound Telnyx webhooks (e.g. an inbound call on this SIP trunk). The
handler verifies the Telnyx Ed25519 signature with the `ed25519` gem **before**
parsing the body, then reads event fields from `data.payload`.

### Request headers

| Header | Required | Description |
|--------|----------|-------------|
| `telnyx-signature-ed25519` | **yes** | Base64 Ed25519 signature of `"<timestamp>\|<raw-body>"` |
| `telnyx-timestamp` | **yes** | Unix-seconds timestamp; rejected if older than 300s (replay protection) |

### Request body

The raw Telnyx webhook envelope:

```json
{
  "data": {
    "event_type": "call.initiated",
    "payload": { "from": "+15551234567", "to": "+15557654321" }
  }
}
```

### Responses

| Status | Meaning |
|--------|---------|
| `200` | Signature verified and event handled (`{"received": true}`) |
| `400` | Missing signature headers or invalid JSON |
| `401` | Invalid signature |
| `408` | Stale timestamp (outside the 300s replay window) |
| `500` | `TELNYX_PUBLIC_KEY` not configured |

---

## Telnyx API Endpoints Called

The application wraps these Telnyx SIP Trunking endpoints via the `telnyx`
Ruby SDK (5.x instance API):

| SDK call | Telnyx endpoint | Used by |
|----------|-----------------|---------|
| `client.credential_connections.create(...)` | `POST /v2/credential_connections` | `POST /sip/connections` |
| `client.credential_connections.list(...)` | `GET /v2/credential_connections` | `GET /sip/connections` |
| `client.credential_connections.retrieve(id)` | `GET /v2/credential_connections/{id}` | `GET /sip/connections/:id` |

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success (retrieve / list / webhook) |
| `201` | Created (new SIP connection) |
| `400` | Bad request — missing or invalid fields / JSON |
| `401` | Invalid API key (or invalid webhook signature) |
| `408` | Stale webhook timestamp |
| `429` | Rate limit exceeded |
| `502` | Upstream Telnyx API error |
| `503` | Network error connecting to Telnyx |
