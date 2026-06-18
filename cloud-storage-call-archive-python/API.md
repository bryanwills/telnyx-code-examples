## `POST /buckets`

Create a new bucket.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/buckets \
  -H "Content-Type: application/json" \
  -d '{"error": "Error description"}'
```

---

## `GET /buckets`

List all buckets.

### Response `200`

```json
{
  "error": "Error description"
}
```

**Try it:**

```bash
curl http://localhost:5000/buckets
```

---

## `POST /archive`

Archive recording.

### Request

```json
{
  "recording_url": "recording-url-value",
  "call_id": "call-id-value",
  "metadata": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `recording_url` | `string` | **yes** | Recording url |
| `call_id` | `string` | no | Call id |
| `metadata` | `object` | no | Metadata |

### Response `200`

```json
{
  "error": "invalid request body"
}
```

**Try it:**

```bash
curl -X POST http://localhost:5000/archive \
  -H "Content-Type: application/json" \
  -d '{"recording_url": "recording-url-value", "call_id": "call-id-value", "metadata": {}}'
```

---

## `POST /webhooks/recording`

Receives Telnyx webhook events.

---

**Try it:**

```bash
curl -X POST http://localhost:5000/webhooks/recording
```

## `GET /archive`

List all archive.

### Response `200`

```json
{"recordings": results[-50:], "total": "<string>"}
```

**Try it:**

```bash
curl http://localhost:5000/archive
```

---

## `GET /archive/search`

Search archive.

### Response `200`

```json
{"results": results[:20], "query": null}
```

**Try it:**

```bash
curl http://localhost:5000/archive/search
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

Records use these status values: `archived`, `ok`, `queued`

## Error Handling

All endpoints return JSON. On error:

```json
{
  "recordings": "example-value",
  "total": 3
}
```

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid fields |
| `500` | Server error |
