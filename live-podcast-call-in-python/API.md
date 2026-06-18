## `POST /shows/start`

Start show.

### Request

```json
{
  "hosts": [],
  "topic": "topic-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `hosts` | `array` | no | Hosts |
| `topic` | `string` | no | Topic |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/shows/start \
  -H "Content-Type: application/json" \
  -d '{"hosts": [], "topic": "topic-value"}'
```

---

## `POST /webhooks/voice`

Receives Telnyx Call Control webhook events. Called automatically by Telnyx during calls — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/voice
```

## `POST /shows/<show_id>/next-caller`

Admit next caller.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/shows/example-id/next-caller \
  -H "Content-Type: application/json" \
  -d '{"error": "invalid request body"}'
```

---

## `POST /shows/<show_id>/fact-check`

Fact check.

### Request

```json
{
  "claim": "claim-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim` | `string` | no | Claim |

### Response `200`

```json
{
  "error": "Show not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/shows/example-id/fact-check \
  -H "Content-Type: application/json" \
  -d '{"claim": "claim-value"}'
```

---

## `GET /shows/<show_id>/queue`

View queue.

### Response `200`

```json
{
  "error": "Show not found"
}
```

**Try it:**

```bash
curl http://localhost:5000/shows/example-id/queue
```

---

## `GET /shows`

List all shows.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/shows
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "active_shows": "example-value",
  "callers_in_queue": "example-value",
  "version": "1.0.0"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `live`, `ok`, `queued`, `rejected`, `screening`

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
