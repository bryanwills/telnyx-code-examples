## `POST /identities`

Add identity.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string` | **yes** | Number |
| `name` | `string` | **yes** | Display name or label |
| `greeting` | `string` | **yes** | Greeting |
| `forward_to` | `string` | **yes** | Forward to |
| `hours` | `string` | no | Hours |

### Response `200`

```json
{"status": "added", "number": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/identities \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /identities`

List all identities.

### Response `200`

```json
{"identities": {k: {"name": v["name"], "hours": v["hours"]}
```

**Try it:**

```bash
curl http://localhost:5000/identities
```

---

## `GET /calls`

List all calls.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/calls
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "identities": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `added`, `answering`, `ended`, `forwarding`, `greeting`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "invalid request body"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
