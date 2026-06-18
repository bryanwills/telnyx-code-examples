## `POST /webhooks/sms`

Receives Telnyx Messaging webhook events. Called automatically by Telnyx for inbound messages — do not call directly.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/sms
```

## `GET /listings`

List all listings.

### Response `200`

```json
{"listings": null}
```

**Try it:**

```bash
curl http://localhost:5000/listings
```

---

## `GET /conversations`

List all conversations.

### Response `200`

```json
{"conversations": conversations[-50:]}
```

**Try it:**

```bash
curl http://localhost:5000/conversations
```

---

## `GET /flagged`

List all flagged.

### Response `200`

```json
{"flagged": null}
```

**Try it:**

```bash
curl http://localhost:5000/flagged
```

---

## `GET /health`

Health check and service status.

### Response `200`

```json
{
  "status": "ok",
  "conversations": "<string>",
  "flagged": "<string>"
}
```

**Try it:**

```bash
curl http://localhost:5000/health
```

---

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
