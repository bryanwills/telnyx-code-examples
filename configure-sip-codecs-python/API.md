## `GET /sip/connections`

List all connections.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl http://localhost:5000/sip/connections
```

---

## `POST /sip/connections`

Create a new connection.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | **yes** | Display name or label |
| `codecs` | `string` | no | Codecs |
| `username` | `string` | **yes** | Username |
| `password` | `string` | **yes** | Password |
| `sip_endpoint` | `string` | **yes** | Sip endpoint |

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/sip/connections \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /sip/connections/<connection_id>`

Get a specific connection by ID.

### Response `200`

```json
{
  "error": "Invalid API key"
}
```

**Try it:**

```bash
curl http://localhost:5000/sip/connections/example-id
```

---

## Error Handling

All endpoints return JSON. On error:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
