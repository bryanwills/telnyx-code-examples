# API Reference — Full-Stack AI Contact Center

Base URL: `http://localhost:5000`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/agents` | Register agent. |
| `POST` | `/webhooks/voice` | Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly. |
| `GET` | `/dashboard` | Dashboard. |
| `GET` | `/queues` | List queues. |
| `GET` | `/recordings` | List recordings. |
| `GET` | `/health` | Health check and service status. |

---

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

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

## `GET /dashboard`

Dashboard.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

---

## `GET /queues`

List all queues.

### Response `200`

```json
{"queues": {k: {"name": v["name"], "agents": "<string>", "waiting": "<string>"}
```

---

## `GET /recordings`

List all recordings.

### Response `200`

```json
{"recordings": recordings[-20:]}
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
