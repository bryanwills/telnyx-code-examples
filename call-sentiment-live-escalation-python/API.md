## `POST /monitor`

Start monitoring.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `call_id` | `string` | **yes** | Call id |
| `agent` | `string` | **yes** | Agent |
| `customer` | `string` | **yes** | Customer |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/monitor \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /transcript`

Receive transcript.

### Request

```json
{
  "error": "invalid request body"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `call_id` | `string` | **yes** | Call id |
| `text` | `string` | no | Text content |
| `speaker` | `string` | no | Speaker |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/transcript \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `GET /calls/<call_id>/sentiment`

Call sentiment.

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/calls/example-id/sentiment
```

---

## `GET /escalations`

List all escalations.

### Response `200`

```json
{"escalations": escalations[-50:]}
```

**Try it:**

```bash
curl http://localhost:5000/escalations
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "monitoring": "<string>",
  "escalations": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `escalated`, `monitoring`, `ok`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "escalations": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
