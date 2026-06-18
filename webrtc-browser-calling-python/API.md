## `POST /token`

Generates a short-lived WebRTC credential token for browser-based calling.

### Request

```json
{
  "connection_id": "your-sip-connection-id"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection_id` | `string` | **yes** | SIP Connection ID from portal |

### Response `200`

```json
{
  "token": "eyJ...",
  "expires_at": "2026-06-18T21:00:00Z"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/token \
  -H "Content-Type: application/json" \
  -d '{"connection_id": "your-sip-connection-id"}'
```

---

## `GET /health`

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl http://localhost:5000/health
```
