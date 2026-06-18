## `POST /episodes/start`

Start episode.

### Request

```json
{
  "title": "title-value",
  "hosts": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | no | Title |
| `hosts` | `array` | no | Hosts |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/episodes/start \
  -H "Content-Type: application/json" \
  -d '{"title": "title-value", "hosts": []}'
```

---

## `POST /episodes/<episode_id>/stop`

Stop episode.

### Response `200`

```json
{
  "error": "Episode not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/episodes/example-id/stop \
  -H "Content-Type: application/json" \
  -d '{"error": "Episode not found"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `GET /episodes`

List all episodes.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/episodes
```

---

## `GET /episodes/<episode_id>`

Get a specific episode by ID.

### Response `200`

```json
{
  "error": "Episode not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/episodes/example-id
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "total_episodes": "example-value",
  "recording": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `complete`, `dialing`, `ok`, `processing`

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
