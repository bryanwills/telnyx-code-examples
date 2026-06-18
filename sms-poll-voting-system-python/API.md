## `POST /polls`

Create a new poll.

### Request

```json
{
  "options": [],
  "question": "question-value"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `options` | `array` | no | Options |
| `question` | `string` | **yes** | Question |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/polls \
  -H "Content-Type: application/json" \
  -d '{"options": [], "question": "question-value"}'
```

---

## `POST /polls/<pid>/broadcast`

Broadcast poll.

### Request

```json
{
  "numbers": [
    "+12125559999"
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numbers` | `array` | no | List of phone numbers |

### Response `200`

```json
{
  "error": "Not found"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/polls/example-id/broadcast \
  -H "Content-Type: application/json" \
  -d '{"numbers": ["+12125559999"]}'
```

---

## `POST /webhooks/messaging`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/messaging
```

## `GET /polls/<pid>/results`

Results.

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl http://localhost:5000/polls/example-id/results
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "polls": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

## Status Values

Records use these status values: `active`, `ignored`, `no_poll`, `ok`, `voted`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "error": "Not found"
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
