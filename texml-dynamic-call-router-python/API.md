## `POST /texml/route`

Route call.

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl -X POST http://localhost:5000/texml/route \
  -H "Content-Type: application/json" \
  -d '{"status": "ok"}'
```

---

## `POST /texml/recording`

Handle recording.

### Response `200`

```json
{ "status": "ok" }
```

**Try it:**

```bash
curl -X POST http://localhost:5000/texml/recording \
  -H "Content-Type: application/json" \
  -d '{"status": "ok"}'
```

---

## `POST /vip`

Add vip.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phone_number` | `string` | **yes** | Phone number |
| `name` | `string` | no | Display name or label |

### Response `200`

```json
{"status": "added", "phone": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/vip \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
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
  "calls": "<string>",
  "vips": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `added`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "calls": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
