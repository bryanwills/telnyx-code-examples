## `GET /screen/<number>`

Screen number.

### Response `200`

```json
{"number": null, "action": "block", "reason": "blocklisted"}
```

**Try it:**

```bash
curl http://localhost:5000/screen/example-id
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `POST /blocklist`

Add to blocklist.

### Request

```json
{
  "number": "number-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | `string` | **yes** | Number |

### Response `200`

```json
{"status": "blocked", "number": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/blocklist \
  -H "Content-Type: application/json" \
  -d '{"number": "number-value"}'
```

---

## `GET /blocklist`

List all blocklist.

### Response `200`

```json
{
  "blocked": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/blocklist
```

---

## `GET /screening-log`

Get a specific log by ID.

### Response `200`

```json
{"log": null}
```

**Try it:**

```bash
curl http://localhost:5000/screening-log
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "screened": "<string>",
  "blocked": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `blocked`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "number": "example-value",
  "action": "block",
  "reason": "blocklisted"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
