## `POST /agents`

Register agent.

### Request

```json
{
  "id": "id-value",
  "name": "Jane Smith",
  "queue": "queue-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `string` | no | Id |
| `name` | `string` | **yes** | Display name or label |
| `queue` | `string` | no | Queue |

### Response `200`

```json
{"agent": null}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/agents \
  -H "Content-Type: application/json" \
  -d '{"id": "id-value", "name": "Jane Smith", "queue": "queue-value"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /dashboard`

Dashboard.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/dashboard
```

---

## `GET /queues`

List all queues.

### Response `200`

```json
{"queues": {k: {"name": v["name"], "agents": "<string>", "waiting": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/queues
```

---

## `GET /recordings`

List all recordings.

### Response `200`

```json
{"recordings": recordings[-20:]}
```

**Try it:**

```bash
curl http://localhost:5000/recordings
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `ai_assist`, `answering`, `available`, `busy`, `connected`, `ended`, `ivr`, `listening`, `ok`, `processed`, `recorded`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "total_calls": "example-value",
  "answered": "example-value",
  "abandoned": "example-value",
  "avg_wait_secs": "example-value",
  "active_calls": "example-value",
  "queues": [],
  "recordings": "example-value"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
