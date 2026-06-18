## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `POST /cloak/<ccid>`

Set cloak.

### Request

```json
{
  "effect": "effect-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `effect` | `string` | no | Effect |

### Response `200`

```json
{"error": f"Unknown effect. Available: {"<string>")}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/cloak/example-id \
  -H "Content-Type: application/json" \
  -d '{"effect": "effect-value"}'
```

---

## `GET /effects`

List all effects.

### Response `200`

```json
{"effects": EFFECTS}
```

**Try it:**

```bash
curl http://localhost:5000/effects
```

---

## `GET /active`

List all active.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/active
```

---

## `GET /log`

Get a specific log by ID.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/log
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `answering`, `cloaking`, `effect_set`, `ended`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "effects": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
